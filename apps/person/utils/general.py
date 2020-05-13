import uuid

def random_string():
    length = 6
    otp_code = uuid.uuid4().hex
    otp_code = otp_code.upper()[0:length]
    return otp_code
