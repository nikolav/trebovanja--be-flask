# import os
import re

from flask import request
from flask import abort
from flask import make_response
from flask import g

from flask_app      import db
from models.users   import Users
from utils.jwtToken import tokenFromRequest
from utils.jwtToken import decode  as jwtTokenDecode
from utils.jwtToken import expired as tokenExpired
from utils.jwtToken import valid   as tokenValid
from config         import PATHS_SKIP_AUTH


def authenticate():
  # @before_request
  
  error = '@error:authenticate'

  # do not redirect `CORS` preflight `OPTIONS` requests, send success/2xx
  if 'OPTIONS' == request.method.upper():
    return abort(make_response('', 200))
  
  # allow open routes
  if any(re.match(p, request.path) for p in PATHS_SKIP_AUTH):
    return

  # @auth
  try:
    # get token/payload from auth header
    token   = tokenFromRequest()
    payload = jwtTokenDecode(token)
    
    uid = payload['id']
    
    # skip token validation if user is
    #  default, no policies, user
    if not Users.is_default(uid):
          
      # abort.401 if token expired
      if tokenExpired(payload):
        raise Exception('access denied')

      # abort.401 if token invalid
      if not tokenValid(token):
        raise Exception('access denied')
    
    # pass if authenticated, valid user in db
    user = db.session.get(Users, uid)
    
    if user:
      
      # cache auth-data `@globals`
      g.access_token         = token
      g.access_token_payload = payload
      g.user                 = user

      # `.success`, run next
      return
  
  except Exception as err:
    error = err

  # 401/unauthenticated otherwise
  return abort(make_response({ 'error': str(error) }, 401))
