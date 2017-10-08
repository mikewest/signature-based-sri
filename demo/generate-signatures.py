from os import path, listdir
from base64 import b64encode
from random import randint
import ed25519
import re

DIR = path.normpath(path.join(__file__, ".."))

'''
Yield each javascript and css file in the directory
'''
def js_files():
  for f in listdir(DIR):
    if path.isfile(f) and f.endswith(".js"):
      yield f

'''
URL-safe base64 encode a binary digest and strip any padding.
'''
def format_digest(digest):
  return b64encode(digest)

'''
Generate an encoded ed25519 signature.
'''
def ed25519_signature(private_public_key, content):
  signature = ed25519.signature(content, *private_public_key)
  return "ed25519-%s" % format_digest(signature)

'''
Generate private + public key pair for ed25519 signatures.
'''
def ed25519_key_pair():
  secret_key = ''.join(chr(randint(0, 255)) for _ in range(0,32))
  public_key = ed25519.publickey(secret_key)
  return (secret_key, public_key)

def main():
  ed25519_key = ed25519_key_pair()
  for file in js_files():
    print "Listing values for %s" % file
    with open(file, "r") as content_file:
      content = content_file.read()
      print "\tEd25519 integrity: %s" % ed25519_signature(ed25519_key, content)
  print "\nEd25519 public key (used above): %s" % format_digest(ed25519_key[1])

if __name__ == "__main__":
  main()
