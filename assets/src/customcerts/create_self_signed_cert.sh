#!/bin/bash

# Source: https://devopscube.com/create-self-signed-certificates-openssl/
# Execute with: `./create_self_signed_cert.sh DOMAIN1 [DOMAIN2] [DOMAIN3] ...`
# Example: ./create_self_signed_cert.sh autodc.dev-seqera.net autoconnect.dev-seqera.net autowave.dev-seqera.net

if [ "$#" -lt 1 ]
then
  echo "Error: No domain name argument provided"
  echo "Usage: Provide one or more domain names as arguments"
  echo "Example: ./create_self_signed_cert.sh autodc.dev-seqera.net autoconnect.dev-seqera.net autowave.dev-seqera.net"
  exit 1
fi

PRIMARY_DOMAIN=$1
CERT_NAME=${PRIMARY_DOMAIN}

# Create root CA private key (separate from certificate)
echo "Creating root CA private key..."
openssl genrsa -out rootCA.key 2048

# Create root CA certificate using the existing private key
echo "Creating root CA certificate..."
openssl req -x509 \
            -new \
            -key rootCA.key \
            -sha256 -days 365 \
            -nodes \
            -subj "/CN=Root CA/C=ES/ST=Catalan/L=Barcelona/O=Seqera/OU=Seqera CX" \
            -out rootCA.crt

# Generate private key for the domain certificate
echo "Generating private key for ${PRIMARY_DOMAIN}..."
openssl genrsa -out ${CERT_NAME}.key 2048

# Create CSR configuration with multiple domains
cat > csr.conf <<EOF
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = ES
ST = Catalan
L = Barcelona
O = Seqera
OU = Seqera CX
CN = ${PRIMARY_DOMAIN}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
EOF

# Add all provided domains to the alt_names section
DNS_COUNT=1
for domain in "$@"; do
    echo "DNS.${DNS_COUNT} = ${domain}" >> csr.conf
    echo "DNS.$((DNS_COUNT + 1)) = www.${domain}" >> csr.conf
    DNS_COUNT=$((DNS_COUNT + 2))
done

# Add IP addresses
cat >> csr.conf <<EOF
IP.1 = 192.168.1.5 
IP.2 = 192.168.1.6
EOF

echo "Creating certificate signing request..."
# Create CSR request using private key
openssl req -new -key ${CERT_NAME}.key -out ${CERT_NAME}.csr -config csr.conf

# Create external config file for the certificate with all domains
cat > cert.conf <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
EOF

# Add all domains to cert.conf as well
DNS_COUNT=1
for domain in "$@"; do
    echo "DNS.${DNS_COUNT} = ${domain}" >> cert.conf
    echo "DNS.$((DNS_COUNT + 1)) = www.${domain}" >> cert.conf
    DNS_COUNT=$((DNS_COUNT + 2))
done

# Add IP addresses to cert.conf
cat >> cert.conf <<EOF
IP.1 = 192.168.1.5
IP.2 = 192.168.1.6
EOF

echo "Creating SSL certificate with self-signed CA..."
# Create SSL certificate with self signed CA
openssl x509 -req \
    -in ${CERT_NAME}.csr \
    -CA rootCA.crt -CAkey rootCA.key \
    -CAcreateserial -out ${CERT_NAME}.crt \
    -days 365 \
    -sha256 -extfile cert.conf

echo "Certificate creation complete!"
echo "Files created:"
echo "  - rootCA.key (Root CA private key)"
echo "  - rootCA.crt (Root CA certificate)"
echo "  - ${CERT_NAME}.key (Domain private key)"
echo "  - ${CERT_NAME}.crt (Domain certificate)"
echo ""
echo "Domains included in certificate:"
for domain in "$@"; do
    echo "  - ${domain}"
    echo "  - www.${domain}"
done
