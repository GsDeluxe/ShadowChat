from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class CryptoHandler():
	def get_random_bytes(self, num=2048) -> bytes:
		return os.urandom(num)

	def generate_key(self, rbytes: bytes):

		salt = b'~4\xb43\xf6.\xc16P\xc7C\x84\n\xc0\x9e\x96'

		kdf = PBKDF2HMAC(
			algorithm=hashes.SHA256(),
			length=32,
			salt=salt,
			iterations=1000,
			backend=default_backend()
		)

		key = kdf.derive(rbytes)

		return key

	def encryption(self, key: bytes, data: bytes):
		try:
			iv = os.urandom(16)

			padder = padding.PKCS7(algorithms.AES.block_size).padder()
			plaintext_padded = padder.update(data) + padder.finalize()

			cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())

			encryptor = cipher.encryptor()
			ciphertext = encryptor.update(plaintext_padded) + encryptor.finalize()

			encoded_text = iv + ciphertext

			return encoded_text

		except Exception as e:
			print("Error Encrypting! " + str(e))

	def decryption(self, key: bytes, cipherdata: bytes):
		try:
			ciphertext = cipherdata

			iv = ciphertext[:16]

			cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
			decryptor = cipher.decryptor()

			decrypted_padded = decryptor.update(ciphertext[16:]) + decryptor.finalize()

			unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
			decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

			return decrypted

		except Exception as e:
			print("Error Decrypting! " + str(e))