# TLS 与零信任认证机制

本文档说明 BlackBerry Passport 自带浏览器接入 `bb10-gateway-core` 时的加密与身份验证规范。

---

## 1. BlackBerry 10 WebKit 的 TLS 规范约束

BlackBerry 10 (`OS 10.3.3.3216`) 搭载的系统级浏览器基于 WebKit 架构 (`AppleWebKit/537.35+`)，具有明确的安全要求：
- **强制 TLS 1.2+**：现代网页和 WebSocket 连接需通过安全 TLS 管道传输。
- **密码套件兼容**：支持现代标准 ECDHE 与 RSA 密码套件。
- **证书信任链**：若为私有自签名证书，BB10 证书信任库将拦截未经授信的叶子证书，必须将自建私有 Root CA 证书导入系统信任根。

---

## 2. 签发私有 Root CA 与服务端证书

为避免 Passport 浏览器每次连接弹出安全证书警告，推荐自建私有根证书体系：

```bash
# 1. 创建私有根证书颁发机构 (Root CA)
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
    -subj "/C=US/O=MyLab/CN=MyLab Root CA" -out ca.crt

# 2. 生成服务端私钥与带 SAN 扩展的证书请求
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/O=MyLab/CN=bb10.local"

# 3. 使用私有根证书签署服务端证书
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

## 3. 在 BlackBerry Passport 上安装根证书

1. 将 `ca.crt` 传送到 Passport 设备（可通过 LocalSend、邮件或 USB 存储）。
2. 在 Passport 上打开 **设置 -> 安全和隐私 -> 证书**。
3. 点击底部操作栏的 **导入**。
4. 选中 `ca.crt`，核对证书信息并勾选 **信任**。
5. 信任后，系统自带浏览器即可平滑、静默建立 HTTPS/WSS 加密连接。

---

## 4. 零信任令牌验证

每个网关服务实例均由专属访问令牌保护：
- **首次连入**：`https://<host>:<port>/?t=<SECRET_TOKEN>`
- **防时序攻击验证**：服务端使用 `hmac.compare_digest` 恒定时间比对令牌。
- **安全 Cookie 签发**：验证通过后自动设置 `HttpOnly`、`SameSite=Lax` 会话 Cookie（90 天有效期）。后续网页交互及 WebSocket 升级自动完成身份验证。
