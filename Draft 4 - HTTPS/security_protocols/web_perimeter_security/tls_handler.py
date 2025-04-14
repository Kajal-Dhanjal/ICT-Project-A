import os

def get_tls_context():
    cert_folder = os.path.join(os.path.dirname(__file__), "certs")
    cert_path = os.path.join(cert_folder, "cert.pem")
    key_path = os.path.join(cert_folder, "key.pem")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        return (cert_path, key_path)
    else:
        raise FileNotFoundError("TLS certificate or key not found.")
