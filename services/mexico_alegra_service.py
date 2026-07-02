"""
Mexico Alegra service - Simplified version for Mexico invoice processing.
"""
import requests
import base64
import logging
from typing import Optional, Dict, Any
from format_utils import format_invoice, format_number_template


logger = logging.getLogger(__name__)


class MexicoAlegraService:
    """Simplified Alegra service for Mexico invoice processing (no PO validation)."""
    
    INVOICES_ENDPOINT = "api/v1/bills"
    CONTACTS_ENDPOINT = "api/v1/contacts"
    DEFAULT_ZIP_CODE = "10400"
    DEFAULT_COUNTRY = "MEX"
    DEFAULT_REGIME = "NO_REGIME"
    DEFAULT_PHONE = "0000000000"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Mexico Alegra Service.
        
        Args:
            config: Alegra configuration dictionary with endpoint, user, token
        """
        self.base_url = config["endpoint"]
        self.user = config["user"]
        self.token = config["token"]
        self.auth = self._generate_auth_header(self.user, self.token)
        self.country = "MX"
        # Catálogo de retenciones de Alegra (se carga 1 vez, no por factura).
        self._retention_catalog = None
        # Tolerancia para hacer match entre el % capturado y el del catálogo.
        self.RETENTION_PCT_TOLERANCE = 0.05
    
    def _generate_auth_header(self, user: str, token: str) -> str:
        """Generate base64 encoded authorization header."""
        auth_str = f"{user}:{token}".encode()
        return base64.b64encode(auth_str).decode()
    
    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Create standard headers for API requests."""
        return {
            "accept": "application/json",
            "authorization": f"Basic {self.auth}",
            "content-type": content_type
        }
    
    def verify_provider_exists(self, issuer_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify if a provider exists in Alegra by their identification number.
        
        Args:
            issuer_id: Provider's identification number (RFC for Mexico)
            
        Returns:
            Provider information if found, None otherwise
        """
        try:
            url = f"{self.base_url}{self.CONTACTS_ENDPOINT}"
            params = {
                "order_direction": "ASC",
                "identification": issuer_id,
                "type": "provider"
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            providers = response.json()
            
            if not providers or len(providers) == 0:
                logger.warning(f"Provider not found in Alegra: {issuer_id}")
                return None
            
            logger.info(f"Provider found in Alegra: {issuer_id}")
            return providers[0]
            
        except Exception as e:
            logger.error(f"Error verifying provider {issuer_id}: {e}", exc_info=True)
            return None

    def _search_contacts(self, params: Dict[str, Any]) -> Optional[list]:
        """Search contacts with given params."""
        try:
            url = f"{self.base_url}{self.CONTACTS_ENDPOINT}"
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json() or []
        except Exception as e:
            logger.error(f"Error searching contacts with params {params}: {e}", exc_info=True)
            return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        return (text or "").strip().lower()

    def find_contact_by_identification(self, identification: str) -> Optional[Dict[str, Any]]:
        """Find a contact by identification, checking provider then client."""
        params = {
            "order_direction": "ASC",
            "identification": identification,
            "type": "provider"
        }
        providers = self._search_contacts(params)
        if providers:
            return providers[0]

        params["type"] = "client"
        clients = self._search_contacts(params)
        if clients:
            return clients[0]

        return None

    def find_contact_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a contact by exact name match (case-insensitive, trimmed)."""
        normalized_target = self._normalize_text(name)

        params = {"order_direction": "ASC", "name": name, "type": "provider"}
        providers = self._search_contacts(params) or []
        for contact in providers:
            if self._normalize_text(contact.get("name")) == normalized_target:
                return contact

        params["type"] = "client"
        clients = self._search_contacts(params) or []
        for contact in clients:
            if self._normalize_text(contact.get("name")) == normalized_target:
                return contact

        return None

    def _validate_zip_code(self, zip_code: str) -> str:
        """Validate zip code format (5 digits). Returns default if invalid."""
        if zip_code and len(zip_code) == 5 and zip_code.isdigit():
            return zip_code
        if zip_code:
            logger.warning(f"Invalid zip code '{zip_code}', using default {self.DEFAULT_ZIP_CODE}")
        return self.DEFAULT_ZIP_CODE

    def create_contact(
        self,
        rfc: str,
        name: str,
        email: str = "",
        address: str = "",
        zip_code: str = "",
        regime: str = "",
        phone: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Create a new contact with basic fields."""
        try:
            url = f"{self.base_url}{self.CONTACTS_ENDPOINT}"
            
            # Use provided values or defaults
            actual_zip = self._validate_zip_code(zip_code)
            actual_regime = regime if regime else self.DEFAULT_REGIME
            actual_phone = phone if phone else self.DEFAULT_PHONE
            
            payload: Dict[str, Any] = {
                "name": name,
                "identification": rfc,
                "type": "provider",
                "phonePrimary": actual_phone,
                "regimeObject": [actual_regime],
                "address": {
                    "country": self.DEFAULT_COUNTRY,
                    "zipCode": actual_zip
                }
            }
            if email:
                payload["email"] = email
            if address:
                payload["address"]["address"] = address

            response = requests.post(url, json=payload, headers=self._get_headers())
            
            # Handle success
            if response.status_code in (200, 201):
                return response.json()
                
            # Handle error
            error_response = {}
            try:
                error_response = response.json()
            except Exception:
                pass
                
            # Check for "Contact already exists" error (code 2006 or similar with contactId)
            # Example: {"message": "Ya existe un contacto...", "code": 2006, "contactId": "1142"}
            if response.status_code == 400 and error_response.get("contactId"):
                conflict_id = str(error_response.get("contactId"))
                logger.warning(
                    f"Create failed but contact exists (ID: {conflict_id}). "
                    f"Attempting to update instead. Error: {error_response.get('message')}"
                )
                
                # Construct a minimal contact dict with the ID to trigger update
                contact_ref = {"id": conflict_id}
                
                # Call update_contact_if_needed
                update_result = self.update_contact_if_needed(
                    contact=contact_ref,
                    rfc=rfc,
                    name=name,
                    email=email,
                    address=address,
                    zip_code=zip_code,
                    regime=regime,
                    phone=phone
                )
                
                if update_result.get("success"):
                    logger.info(f"Successfully recovered from creation error by updating contact {conflict_id}")
                    # Return a mock representation of the contact to satisfy the return type
                    return {"id": conflict_id, "recovered": True}
                else:
                    logger.error(f"Failed to recover/update contact {conflict_id}")
                    return None

            logger.error(
                f"Failed to create contact. Status: {response.status_code}, Response: {response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error creating contact {rfc}: {e}", exc_info=True)
            return None

    def update_contact_if_needed(
        self,
        contact: Dict[str, Any],
        rfc: str,
        name: str,
        email: str = "",
        address: str = "",
        zip_code: str = "",
        regime: str = "",
        phone: str = ""
    ) -> Dict[str, Any]:
        """Update contact if any field differs. Returns contact data + action."""
        contact_id = contact.get("id")
        if not contact_id:
            return {"id": None, "action": "error"}

        existing_name = (contact.get("name") or "").strip()
        existing_rfc = (contact.get("identification") or "").strip()
        existing_email = (contact.get("email") or "").strip()
        existing_address = ((contact.get("address") or {}).get("address") or "").strip()
        existing_zip = ((contact.get("address") or {}).get("zipCode") or "").strip()
        existing_phone = (contact.get("phonePrimary") or "").strip()
        existing_regime = (contact.get("regimeObject") or [self.DEFAULT_REGIME])
        if isinstance(existing_regime, list) and len(existing_regime) > 0:
            existing_regime = existing_regime[0]
        else:
            existing_regime = self.DEFAULT_REGIME
        existing_type = contact.get("type")

        payload: Dict[str, Any] = {}
        updated = False

        if name and name != existing_name:
            payload["name"] = name
            updated = True
        else:
            payload["name"] = existing_name

        if rfc and rfc != existing_rfc:
            payload["identification"] = rfc
            updated = True
        else:
            payload["identification"] = existing_rfc

        if email:
            if email != existing_email:
                payload["email"] = email
                updated = True
            else:
                payload["email"] = existing_email
        else:
            if existing_email:
                payload["email"] = existing_email

        # Handle zip code
        # Use existing zip if available and valid? Or just validate input
        # If input zip is provided, validate it. If valid, use it. If invalid, use default.
        # If input zip is NOT provided, check existing. If existing is valid, keep it. Else default.
        
        target_zip = zip_code if zip_code else existing_zip
        actual_zip = self._validate_zip_code(target_zip)
        
        address_payload = {
            "country": self.DEFAULT_COUNTRY,
            "zipCode": actual_zip
        }
        
        if actual_zip != existing_zip:
            updated = True
            
        if address:
            if address != existing_address:
                address_payload["address"] = address
                updated = True
            else:
                address_payload["address"] = existing_address
        else:
            if existing_address:
                address_payload["address"] = existing_address

        if address_payload.get("address") is not None or actual_zip:
            payload["address"] = address_payload

        # If contact is only client, switch to provider
        if existing_type == "client":
            payload["type"] = "provider"
            updated = True
        elif existing_type:
            payload["type"] = existing_type

        # Handle phone
        actual_phone = phone if phone else (existing_phone if existing_phone else self.DEFAULT_PHONE)
        if phone and phone != existing_phone:
            updated = True
        payload["phonePrimary"] = actual_phone
        
        # Handle regime
        actual_regime = regime if regime else existing_regime
        if regime and regime != existing_regime:
            updated = True
        payload["regimeObject"] = [actual_regime]

        if not updated:
            return {"id": str(contact_id), "action": "unchanged"}

        try:
            url = f"{self.base_url}{self.CONTACTS_ENDPOINT}/{contact_id}"
            response = requests.put(url, json=payload, headers=self._get_headers())
            if response.status_code not in (200, 201):
                logger.error(
                    f"Failed to update contact {contact_id}. Status: {response.status_code}, Response: {response.text}"
                )
                return {"id": str(contact_id), "action": "error", "success": False}

            updated_contact = response.json()
            return {"id": str(updated_contact.get("id", contact_id)), "action": "updated", "success": True}
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}", exc_info=True)
            return {"id": str(contact_id), "action": "error", "success": False}
    
    def check_duplicate_invoice(self, document_id: str, provider_id: str) -> bool:
        """
        Check if an invoice already exists in Alegra.
        
        Args:
            document_id: Invoice document number/UUID
            provider_id: Provider's Alegra ID
            
        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            url = f"{self.base_url}{self.INVOICES_ENDPOINT}"
            params = {"number": document_id}
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            invoices = response.json()
            
            if not invoices or len(invoices) == 0:
                return False
            
            # Check if any invoice matches both document_id and provider_id
            for invoice in invoices:
                invoice_number = invoice.get("numberTemplate", {}).get("number")
                invoice_provider_id = str(invoice.get("provider", {}).get("id"))
                
                if invoice_number == document_id and invoice_provider_id == str(provider_id):
                    logger.warning(
                        f"Duplicate invoice found: {document_id} "
                        f"(Alegra ID: {invoice.get('id')})"
                    )
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate invoice: {e}", exc_info=True)
            return False
    
    def _load_retention_catalog(self) -> list:
        """Carga el catálogo de retenciones de Alegra UNA sola vez (cacheado).

        Devuelve una lista de dicts {id, type, percentage(float)} de las
        retenciones activas. Se consulta una vez por corrida (no por factura),
        de modo que los IDs no se queman en código y se adaptan si Alegra cambia.
        """
        if self._retention_catalog is not None:
            return self._retention_catalog

        url = f"{self.base_url}api/v1/retentions"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json() or []
            catalog = []
            for r in data:
                if r.get("status") and r.get("status") != "active":
                    continue
                try:
                    pct = round(float(r.get("percentage", 0)), 2)
                except (TypeError, ValueError):
                    continue
                catalog.append({
                    "id": str(r.get("id")),
                    "type": (r.get("type") or "").upper(),
                    "percentage": pct,
                    "name": r.get("name", ""),
                })
            self._retention_catalog = catalog
            logger.info(f"Catálogo de retenciones Alegra cargado: {len(catalog)} entradas")
            return catalog
        except Exception as e:
            logger.error(f"Error cargando catálogo de retenciones: {e}", exc_info=True)
            self._retention_catalog = []
            return self._retention_catalog

    def resolve_retention_id(self, tax_type: str, amount: float, subtotal: float) -> Optional[str]:
        """Resuelve el ID de retención de Alegra para (tipo, monto, base).

        Calcula el % = amount/subtotal y busca en el catálogo una retención del
        mismo tipo con ese % (dentro de la tolerancia). Devuelve el id o None si
        no hay match (la factura se saltará y se reportará; no se adivina).
        """
        if not subtotal or subtotal <= 0 or not amount or amount <= 0:
            return None
        catalog = self._load_retention_catalog()
        if not catalog:
            return None
        pct = round(amount / subtotal * 100, 2)
        tax_type = (tax_type or "").upper()

        candidates = [
            c for c in catalog
            if c["type"] == tax_type and abs(c["percentage"] - pct) <= self.RETENTION_PCT_TOLERANCE
        ]
        if not candidates:
            logger.warning(
                f"Retención sin match en catálogo: tipo={tax_type} monto={amount} "
                f"base={subtotal} (~{pct}%)"
            )
            return None
        # Si hay más de una (p. ej. ISR 10% tiene 2 IDs), tomar la primera (menor id).
        candidates.sort(key=lambda c: int(c["id"]))
        return candidates[0]["id"]

    def create_invoice(self, analyzed_data: Dict[str, Any], provider_info: Dict[str, Any], xml_file_path: str = None) -> Optional[Dict[str, Any]]:
        """
        Create invoice in Alegra for Mexico.
        
        Args:
            analyzed_data: Data extracted from invoice
            provider_info: Provider information from Alegra
            xml_file_path: Path to XML file to attach (optional)
            
        Returns:
            Created invoice information, or None if failed
        """
        try:
            # Create attachment structure (simulated for format_invoice)
            attachment = {
                "analyzed_data": analyzed_data,
                "filename": xml_file_path.split("/")[-1] if xml_file_path else "invoice.xml",
                "data": None  # Will be loaded when attaching
            }
            
            # Check for account override (from Excel mode)
            # Create fake PO if override exists to pass account name to format_utils
            account_name = analyzed_data.get("account_name_override")
            fake_po = None
            if account_name:
                fake_po = {
                    "purchases": {
                        "categories": [
                            {"name": account_name}
                        ]
                    }
                }
            
            # Format the invoice payload
            payload = format_invoice(
                attachment=attachment,
                analyzed_data=analyzed_data,
                provider_information=[provider_info],
                alegra_client=self,
                country=self.country,
                purchase_order=fake_po  # Pass fake PO if needed, else None
            )
            
            if not payload:
                logger.error("Failed to format invoice payload")
                return None
            
            # Log payload for debugging
            import json
            logger.info(f"Payload for invoice: {json.dumps(payload)}")

            # Create invoice in Alegra
            url = f"{self.base_url}{self.INVOICES_ENDPOINT}"
            response = requests.post(url, json=payload, headers=self._get_headers())
            
            if response.status_code != 201:
                logger.error(
                    f"Failed to create invoice. Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                return None
            
            invoice_data = response.json()
            logger.info(f"Invoice created successfully. Alegra ID: {invoice_data.get('id')}")
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return None
    
    def attach_file_to_invoice(self, invoice_id: str, xml_file_path: str) -> bool:
        """
        Attach XML file to an invoice in Alegra.
        
        Args:
            invoice_id: Alegra invoice ID
            xml_file_path: Path to the XML file
            
        Returns:
            True if attachment successful, False otherwise
        """
        try:
            # Read XML file
            with open(xml_file_path, 'rb') as f:
                xml_data = f.read()
            
            filename = xml_file_path.split("/")[-1]
            
            url = f"{self.base_url}{self.INVOICES_ENDPOINT}/{invoice_id}/attachment"
            files = {"file": (filename, xml_data, "application/xml")}
            headers = {
                "accept": "application/json",
                "authorization": f"Basic {self.auth}"
            }
            
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()
            
            logger.info(f"File attached to invoice {invoice_id}: {filename}")
            return True
            
        except Exception as e:
            logger.error(
                f"Error attaching file to invoice {invoice_id}: {e}",
                exc_info=True
            )
            return False
    
    def add_comment_to_invoice(self, invoice_id: str, comment: str) -> bool:
        """
        Add a comment to an invoice in Alegra.
        
        Args:
            invoice_id: Alegra invoice ID
            comment: Comment text
            
        Returns:
            True if comment added successfully, False otherwise
        """
        try:
            url = f"{self.base_url}{self.INVOICES_ENDPOINT}/{invoice_id}/comments"
            payload = {"comments": [comment]}
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            logger.info(f"Comment added to invoice {invoice_id}")
            return True
            
        except Exception as e:
            logger.error(
                f"Error adding comment to invoice {invoice_id}: {e}",
                exc_info=True
            )
            return False
    
    def _get_countable_account_by_name(self, account_name: str) -> Optional[str]:
        """
        Get account ID by name (required for format_invoice compatibility).
        
        Args:
            account_name: Account name to search for
            
        Returns:
            Account ID if found, None otherwise
        """
        try:
            url = f"{self.base_url}api/v1/categories"
            params = {"format": "plain", "name": account_name}
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            accounts = response.json()
            
            if not accounts:
                logger.warning(f"Account not found: {account_name}")
                return None
            
            # Use the existing find_id_by_name function
            from format_utils import find_id_by_name
            account_id = find_id_by_name(accounts, account_name)
            
            if account_id:
                logger.info(f"Account found: {account_name} (ID: {account_id})")
            
            return account_id
            
        except Exception as e:
            logger.error(f"Error getting account by name {account_name}: {e}", exc_info=True)
            return None
