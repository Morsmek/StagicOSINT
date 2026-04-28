"""
SSL Certificate Transforms
  - SslCertificate:  Domain/IPAddress -> SSLCertificate + Subject/SANs
"""
import asyncio
import ssl
import socket
from datetime import datetime

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult


class SslCertificate(BaseTransform):
    NAME = "ssl_certificate"
    DISPLAY_NAME = "SSL Certificate"
    DESCRIPTION = "Fetch and parse the SSL/TLS certificate from a domain or IP."
    INPUT_TYPES = [EntityType.DOMAIN, EntityType.IP_ADDRESS, EntityType.SUBDOMAIN]
    OUTPUT_TYPES = [EntityType.SSL_CERTIFICATE, EntityType.DOMAIN, EntityType.ORGANIZATION]
    OPTIONS_SCHEMA = {
        "port": {"type": "integer", "default": 443, "description": "Port to connect on"}
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        host = entity["value"]
        port = int(options.get("port", 443))
        entities: list[Entity] = []
        edges: list[Edge] = []
        messages: list[str] = []

        try:
            loop = asyncio.get_event_loop()
            cert = await loop.run_in_executor(None, lambda: self._get_cert(host, port))

            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            not_after = cert.get("notAfter", "")
            not_before = cert.get("notBefore", "")
            san_list = [v for (t, v) in cert.get("subjectAltName", []) if t == "DNS"]

            # Main cert entity
            cn = subject.get("commonName", host)
            cert_entity = self._make_entity(
                EntityType.SSL_CERTIFICATE, cn,
                issuer=issuer.get("organizationName", ""),
                issuer_cn=issuer.get("commonName", ""),
                not_before=not_before,
                not_after=not_after,
                subject_org=subject.get("organizationName", ""),
                san_count=len(san_list),
            )
            entities.append(cert_entity)
            edges.append(self._make_edge(entity["id"], cert_entity.id, "has_certificate"))
            messages.append(f"Certificate: {cn}, expires {not_after}")

            # Subject org
            org_name = subject.get("organizationName")
            if org_name:
                org_entity = self._make_entity(EntityType.ORGANIZATION, org_name)
                entities.append(org_entity)
                edges.append(self._make_edge(cert_entity.id, org_entity.id, "issued_to"))

            # SANs as domains
            for san in san_list[:20]:  # Cap at 20
                san_clean = san.lstrip("*.")
                if san_clean and san_clean != host:
                    domain_entity = self._make_entity(EntityType.DOMAIN, san_clean, source="ssl_san")
                    entities.append(domain_entity)
                    edges.append(self._make_edge(cert_entity.id, domain_entity.id, "san"))

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, messages)

    @staticmethod
    def _get_cert(host: str, port: int) -> dict:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return ssock.getpeercert()
