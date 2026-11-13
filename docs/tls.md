# TLS & Zero-Trust Authentication

This document outlines the cryptographic and authentication requirements for connecting the BlackBerry Passport stock browser to `bb10-gateway-core`.

---

## 1. BlackBerry 10 WebKit TLS Constraints

The stock browser on BlackBerry 10 (`OS 10.3.3.3216`) runs a WebKit build (`AppleWebKit/537.35+`) with specific TLS requirements:
- **TLS 1.2+ Required**: Modern web standards and WebSocket streams mandate secure TLS channels.
- **Cipher Support**: Modern ECDHE and RSA cipher suites are supported.
- **Certificate Trust**: The BB10 OS certificate store rejects connections with untrusted self-signed leaf certificates unless the signing Certificate Authority (CA) root certificate is installed into the device trust store.

---

## 2. Generating a Private Root CA and Server Certificate

To avoid browser security warnings on the Passport, establish a private internal CA:

```bash
# 1. Create a private Certificate Authority (CA)
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
    -subj "/C=US/O=MyLab/CN=MyLab Root CA" -out ca.crt

# 2. Generate server private key and CSR with Subject Alternative Name (SAN)
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/O=MyLab/CN=bb10.local"

# 3. Sign server certificate with your CA
cat <<EOF > san.ext
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = bb10.local
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out server.crt -days 825 -sha256 -extfile san.ext
```

---

## 3. Installing Root CA on BlackBerry Passport

1. Transfer `ca.crt` to the Passport (via LocalSend, email, or USB storage).
2. On the Passport, open **Settings -> Security and Privacy -> Certificates**.
3. Tap **Import** in the bottom action bar.
4. Select `ca.crt`, review the certificate details, and tap **Trust**.
5. Once trusted, the stock browser connects to the gateway over HTTPS/WSS without warning dialogs.

---

## 4. Zero-Trust Token Authentication

Every gateway instance requires authentication via secret token:
- **Initial Request**: `https://<host>:<port>/?t=<SECRET_TOKEN>`
- **Constant-Time Verification**: Validated in Python using `hmac.compare_digest` to prevent timing attacks.
- **Cookie Issuance**: Upon successful verification, the gateway sets an `HttpOnly`, `SameSite=Lax` session cookie (`90-day` lifetime). Subsequent requests and WebSocket upgrades from the Passport browser authenticate automatically via this cookie.
