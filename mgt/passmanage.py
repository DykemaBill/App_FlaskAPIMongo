import sys, bcrypt
from base64 import b64encode

# Encode and decode passwoards
def passhash(password, salt):
    if password:
        # Encode the password
        pass_encoded = b64encode(password.encode("utf-8"))
        # Create hash of the password using the salt
        pass_hashed = bcrypt.hashpw(pass_encoded, salt)
        # Decode password hashed to make it easier to store
        pass_hashed_decoded = pass_hashed.decode("utf-8")
        # Return hash password, first 29 characters are the salt
        return pass_hashed_decoded

# Get command line arguments
if __name__ == "__main__":
    if (len(sys.argv) == 3) and (sys.argv[1] == "--hash"):
        yourPass = sys.argv[1]
        pass_salt = bcrypt.gensalt()
        yourHash = passhash(yourPass, pass_salt)
        print ("Here is your hashed password:", yourHash)
    elif (len(sys.argv) == 4) and (sys.argv[1] == "--check"):
        yourPass = sys.argv[1]
        pass_salt = sys.argv[2]
        yourHash = passhash(yourPass, pass_salt)
        print ("Here is your hashed password:", yourHash)
    else:
        print ("Syntax:")
        print ("        " + sys.argv[0] + " --hash [password]")
        print ("        " + sys.argv[0] + " --check [password] [salt]")