import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keys(path: str):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    folder = path.rsplit("/", maxsplit=1)[0]
    os.makedirs(folder, exist_ok=True)

    with open(path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


if __name__ == "__main__":
    generate_rsa_keys("/edcurve/secrets/rsa/private.pem")
