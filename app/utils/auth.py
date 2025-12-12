from fastapi import Header, HTTPException

def get_user_id_from_header(x_user_id: str = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID missing in request header")
    return x_user_id
