import json
from services.webhook_service import send_message_to_webhook
import re
import datetime

def load_config():
    with open("config.json") as config_file:
        return json.load(config_file)

config = load_config()

def format_invoice(attachment,analyzed_data, provider_information, alegra_client, country, purchase_order):
    """Generates the JSON payload for creating an invoice."""
    try:
        # # Obtener la letra del documento
        letter = attachment.get("letter", None)
        if country in ["AR"]:
            account = purchase_order.get("purchases", {}).get("categories", [])[0].get("name", None) if purchase_order else None
            if not account and letter:
                if letter == "A":
                    account = "Logística en flete - Agencia"
                elif letter == "C":
                    account = "Logística en flete - Autónomos"
                else:
                    account = "Cuenta contable no reconocida"
            attachment["account"] = account
        elif country in ["PE"]:
            account = "92.6.3.1103"
            account = purchase_order.get("purchases", {}).get("categories", [])[0].get("name", account)
            attachment["account"] = account
        elif country in ["MX"]:
            account = purchase_order.get("purchases", {}).get("categories", [])[0].get("name", None)
            attachment["account"] = account
        categories = []

        # Due date
        due_date = None
        if country == 'AR':
            due_date = purchase_order.get('deliveryDate', get_due_date(analyzed_data))
        else:
            due_date = get_due_date(analyzed_data)

        # Validar que due_date no sea menor que document_date
        document_date = analyzed_data.get("document_data", {}).get("document_information", {}).get("document_date", purchase_order.get("deliveryDate", None))
        if due_date and document_date and due_date < document_date:
            print(f"Advertencia: due_date ({due_date}) es menor que document_date ({document_date}). Usando document_date como due_date.")
            due_date = document_date
        
        # Validar formato de fechas
        if not is_valid_date(document_date) and is_valid_date(due_date):
            print(f"Advertencia: date '{document_date}' no es válido, usando dueDate '{due_date}' como date.")
            document_date = due_date

        if not is_valid_date(due_date) and is_valid_date(document_date):
            print(f"Advertencia: dueDate '{due_date}' no es válido, usando date '{document_date}' como dueDate.")
            due_date = document_date

        if not is_valid_date(document_date) and not is_valid_date(due_date):
            # Usar la fecha actual si ambos formatos son inválidos
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            send_message_to_webhook(
                f"Formato de fecha inválido para date y dueDate: date={document_date}, dueDate={due_date}. Se usará la fecha actual: {current_date}"
            )
            document_date = current_date
            due_date = current_date

        # Verificar si analyzed_data tiene items válidos, si no y es PE, extraer de purchase_order
        items_to_process = analyzed_data["document_data"]["items"]
        if not _has_valid_items(items_to_process) and country in ["PE"] and purchase_order:
            items_to_process = _extract_items_from_purchase_order(purchase_order)

        # Para Perú: Verificar y asignar impuestos desde el nivel de factura si no están en los items
        tax_details = []  # Mover esta declaración fuera del if
        if country == "PE":
            taxes = analyzed_data["document_data"].get("taxes", [])
            total_tax = analyzed_data["document_data"]["document_information"].get("total_tax", 0)
            subtotal = analyzed_data["document_data"]["document_information"].get("subtotal", 0)

            # Calcular tax_rate si no está presente en los items
            if taxes and not any(item.get("tax_rate") for item in items_to_process):
                # Procesar todos los impuestos en el arreglo `taxes`
                for tax in taxes:
                    tax_rate = tax.get("tax_rate")
                    tax_amount = tax.get("tax_amount")
                    
                    # Si no hay tax_rate, calcularlo usando tax_amount y subtotal
                    if tax_rate is None and tax_amount and subtotal:
                        tax_rate = (tax_amount / subtotal) * 100
                    
                    # Redondear a dos decimales para coincidir con el config.json
                    if tax_rate is not None:
                        tax_rate = round(tax_rate, 2)
                        # Convertir a decimal (0.18) para que format_tax lo procese correctamente
                        tax_rate_decimal = tax_rate / 100
                        tax_details.append({
                            "rate": tax_rate,
                            "id": format_tax(tax_rate_decimal, country)
                        })

        for index, item in enumerate(items_to_process):
            item_id = alegra_client._get_countable_account_by_name(account)
            subtotal = item.get("subtotal", item.get("total", None))
            price = item.get("unit_price", subtotal) if country in ["AR"] else item.get("unit_price", item.get("price", subtotal))
            if price == 0 or price is None or price == '':
                price = subtotal
            quantity = item.get("quantity", 1) if country in ["AR"] else item.get("quantity", 1)
            if quantity == 0 or quantity is None or quantity == '' or quantity < 0:
                quantity = 1
            discount = item.get("discount", 0)
            
            # Para Perú: usar tax_details si fue calculado desde el nivel de factura
            if tax_details and country == "PE":
                item_taxes = [{"id": td["id"]} for td in tax_details]
            else:
                # Comportamiento original para otros países
                tax_rate = float(item.get("tax_rate", 0)) / 100 if item.get("tax_rate") else 0
                item_taxes = [{"id": format_tax(tax_rate, country)}]

            # Para Argentina, obtener observations del campo description de purchase_order
            observations = None
            if country in ["AR"] and purchase_order:
                observations = _get_observations_for_argentina(purchase_order, index)
            
            # Si no se obtuvieron observations de purchase_order o no es Argentina, usar el comportamiento original
            if observations is None:
                observations = item.get("description", item.get("observations", None))

            categories.append({
                "id": item_id,
                "discount": discount,
                "observations": observations,
                "tax": item_taxes,
                "price": price,
                "quantity": quantity,
            })
        # Resultado final
        payload = {
            "date": document_date,
            "dueDate": due_date,
            "numberTemplate": {"number": format_number_template(analyzed_data["document_data"]["document_information"]["document_id"],attachment.get("point_of_sale", None), attachment.get("letter", None), country) },
            "provider": {"id": provider_information[0]['id']},
            "total": analyzed_data["document_data"]["document_information"]["total"],
            "warehouse": {"id": "1"},
            # "costCenter": {"id": "6"} if country in ['PE'] else {"id": "15"},  # ID del centro de costos
            "purchases": {"categories": categories}
        }

        # MX: agregar retenciones (ISR/IVA) resolviendo el id contra el catálogo
        # de Alegra. Base para el % = subtotal de la factura. Si alguna retención
        # no se puede mapear, NO se crea la factura (se retorna None) para no
        # cargarla con un monto incorrecto — se reporta y se revisa manualmente.
        retentions_input = analyzed_data["document_data"].get("retentions_input", []) or []
        if country == "MX" and retentions_input:
            base = analyzed_data["document_data"]["document_information"].get("subtotal", 0) or 0
            retentions_payload = []
            for ret in retentions_input:
                rid = alegra_client.resolve_retention_id(ret.get("tax_type"), ret.get("amount"), base)
                # Opción B (DAPYR): retención de IVA cuya base no es el subtotal
                # (IVA 4% sobre el flete). El % monto/subtotal no mapea; se usa el
                # renglón de IVA 4% con el monto EXACTO (Alegra respeta el amount).
                if not rid and (ret.get("tax_type") or "").upper() == "IVA":
                    rid = alegra_client.resolve_iva_retention_fallback(ret.get("amount"))
                    if rid:
                        print(f"Retención IVA base especial → IVA 4% (Opción B): {ret}")
                if not rid:
                    send_message_to_webhook(
                        f"Retención NO mapeada — factura {analyzed_data['document_data']['document_information']['document_id']} "
                        f"NO se cargará. Tipo={ret.get('tax_type')} monto={ret.get('amount')} base={base}. "
                        f"Revisar el tipo/monto de la retención en el archivo."
                    )
                    print(f"Retención no mapeada, se salta la factura: {ret}")
                    return None
                retentions_payload.append({"id": rid, "amount": ret.get("amount")})
            if retentions_payload:
                payload["retentions"] = retentions_payload

        return payload
    except Exception as e:
        send_message_to_webhook(f"Error al crear el formato de la factura de Alegra {analyzed_data['document_data']['document_information']['document_id']}: {e}")
        print(f"Error al crear el formato de la factura {e}")
        return None
    
def format_tax(tax_rate, country):
    """Homologates the taxes from the analyzed data to the Alegra format."""
    taxes = config["erp"]["Alegra"][country]["tax_map"]
    
    # Normalizar el formato del impuesto a porcentaje entero.
    normalized_rate = round(tax_rate * 100, 2)  # Convertir 0.21 a 21.00
    
    for tax in taxes:
        if float(tax['percentage']) == normalized_rate:
            return tax['id']
    
    # Loggear el error si no se encuentra un match.
    send_message_to_webhook(f"Error al homologar el impuesto {tax_rate} del pais {country}")
    return None

def format_number_template(document_id, point_of_sale, letter, country):
    """
    Formatea el número de plantilla basado en el ID del documento, punto de venta y letra.

    Args:
        document_id (str): ID del documento.
        point_of_sale (str): Punto de venta.
        letter (str): Letra del documento.

    Returns:
        str: Número de plantilla formateado o None si la letra no es 'A' o 'C'.
    """
    if country in ["AR"]:
        if not point_of_sale or not letter:
            send_message_to_webhook(f"Error al formatear el número de factura en Alegra: Punto de venta o letra no encontrados Document id:{document_id} Punto de venta: {point_of_sale} Letra: {letter}")
            return None
        if letter == 'A':
            prefix = 'FCA'
        elif letter == 'C':
            prefix = 'FCC'
        else:
            send_message_to_webhook(f"Error al formatear el número de factura en Alegra: Letra no válida. Letra: {letter}")
            return None
        return f"{prefix}{point_of_sale}-{document_id}"
    else:
        return document_id

# Función recursiva para buscar el id de la cuenta contable por nombre
def find_id_by_name(data, target_name):
    if target_name is None or data is None or not data or not target_name:
        return None
    for item in data:
        name = item.get("name") or ""
        code = item.get("code") or ""
        if (target_name.strip() in name.strip() or 
            target_name.strip() == code.strip()):
            return item.get("id")
        if "children" in item:
            result = find_id_by_name(item["children"], target_name)
            if result:
                return result
    return None

def _has_valid_items(items):
    """
    Verifica si los items del analyzed_data tienen datos válidos/útiles.
    
    Args:
        items (list): Lista de items del analyzed_data
        
    Returns:
        bool: True si hay items con datos válidos, False si están vacíos o con valores null
    """
    if not items or len(items) == 0:
        return False
    
    for item in items:
        # Verificar si al menos uno de los campos críticos tiene un valor válido
        critical_fields = ['unit_price', 'quantity', 'subtotal', 'total']
        has_valid_data = any(
            item.get(field) is not None and item.get(field) != '' 
            for field in critical_fields
        )
        
        # Si encontramos al menos un item con datos válidos, retornamos True
        if has_valid_data:
            return True
    
    return False

def _extract_items_from_purchase_order(purchase_order):
    """
    Extrae los items de una orden de compra y los convierte al formato esperado por format_invoice.
    
    Args:
        purchase_order (dict): Orden de compra de Alegra
        
    Returns:
        list: Lista de items en el formato esperado
    """
    if not purchase_order or not purchase_order.get("purchases", {}).get("categories"):
        return []
    
    items = []
    for category in purchase_order["purchases"]["categories"]:
        # Extraer información del impuesto
        tax_rate = 0
        if category.get("tax") and len(category["tax"]) > 0:
            tax_percentage = category["tax"][0].get("percentage", "0.00")
            tax_rate = float(tax_percentage)
        
        item = {
            "unit_price": float(category.get("price", 0)),
            "price": float(category.get("price", 0)),
            "quantity": float(category.get("quantity", 1)),
            "discount": float(category.get("discount", 0)),
            "tax_rate": tax_rate,
            "description": category.get("observations", ""),
            "observations": category.get("observations", ""),
        }
        items.append(item)
    
    return items

def get_document_date(analyzed_data):
    """Extrae la fecha del documento de los datos analizados."""
    doc_info = analyzed_data.get("document_data", {}).get("document_information", {})
    return doc_info.get("document_date", None)

def is_valid_date(date_str):
    # Acepta solo formato YYYY-MM-DD
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(date_str)))

def get_due_date(analyzed_data):
    """Extrae la fecha de vencimiento de los datos analizados."""
    doc_info = analyzed_data.get("document_data", {}).get("document_information", {})
    document_date = doc_info.get("document_date", None)
    due_date = doc_info.get("due_date", document_date)

    # Validar que due_date no sea menor que document_date
    if due_date and document_date and due_date < document_date:
        print(f"Advertencia: due_date ({due_date}) es menor que document_date ({document_date}). Usando document_date como due_date.")
        return document_date

    return due_date

def _get_observations_for_argentina(purchase_order, item_index):
    """
    Obtiene las observations del campo observations de la purchase order para Argentina.
    Busca tanto en "categories" como en "items" según la estructura disponible.
    
    Args:
        purchase_order (dict): Orden de compra de Alegra
        item_index (int): Índice del item en la lista
        
    Returns:
        str: Observations del item en purchase_order o None si no se encuentra
    """
    try:
        if not purchase_order or not purchase_order.get("purchases"):
            return None
        
        purchases = purchase_order["purchases"]
        
        # Primero intentar buscar en "categories"
        if purchases.get("categories"):
            purchase_items = purchases["categories"]
            if item_index < len(purchase_items):
                return purchase_items[item_index].get("observations", None)
        
        # Si no encuentra en "categories", buscar en "items"
        if purchases.get("items"):
            purchase_items = purchases["items"]
            if item_index < len(purchase_items):
                return purchase_items[item_index].get("observations", None)
        
        return None
    except Exception as e:
        send_message_to_webhook(f"Error al obtener observations de purchase order para Argentina: {e}")
        return None