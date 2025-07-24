#! /bin/bash

# SOurce: https://devopscube.com/create-self-signed-certificates-openssl/
# July 24/25: Updated with Claude.ai help to support multiple domains
# Execute with: `./create_self_signed_cert.sh SP_URL OTHER_URL(s)...

if [ "$#" -eq 0 ]
then
  echo "Error: No domain name argument provided"
  echo "Usage: Provide a domain name as an argument"
  exit 1
fi

# DOMAIN=$1
DOMAINS=("$@")
# Use the first domain as the primary domain for file naming
PRIMARY_DOMAIN=${DOMAINS[0]}

# Create root CA & Private key

openssl req -x509 \
            -sha256 -days 356 \
            -nodes \
            -newkey rsa:2048 \
            -subj "/CN=${PRIMARY_DOMAIN}/C=CX/L=Barcelona" \
            -keyout rootCA.key -out rootCA.crt 

# Generate Private key 

openssl genrsa -out ${PRIMARY_DOMAIN}.key 2048

# Create csf conf

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
EOF

# Add all domains to the alt_names section
for i in "${!DOMAINS[@]}"; do
    echo "DNS.$((i+1)) = ${DOMAINS[i]}" >> csr.conf
done

# Add the IP addresses
cat >> csr.conf <<EOF
IP.1 = 192.168.1.5 
IP.2 = 192.168.1.6
EOF

# create CSR request using private key

openssl req -new -key ${PRIMARY_DOMAIN}.key -out ${PRIMARY_DOMAIN}.csr -config csr.conf

# Create a external config file for the certificate

cat > cert.conf <<EOF

authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
EOF

# Add all domains to the cert.conf alt_names section
for i in "${!DOMAINS[@]}"; do
    echo "DNS.$((i+1)) = ${DOMAINS[i]}" >> cert.conf
done

# Create SSl with self signed CA
openssl x509 -req \
    -in ${PRIMARY_DOMAIN}.csr \
    -CA rootCA.crt -CAkey rootCA.key \
    -CAcreateserial -out ${PRIMARY_DOMAIN}.crt \
    -days 365 \
    -sha256 -extfile cert.conf

echo "The certificate supports the following domains:"
for domain in "${DOMAINS[@]}"; do
    echo "  - ${domain}"
done
