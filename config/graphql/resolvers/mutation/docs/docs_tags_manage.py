import os

from flask_app import db
from flask_app import io

from models.tags import Tags
from models.docs import Docs

from config.graphql.init import mutation
from . import IOEVENT_DOCS_TAGS_CHANGE_prefix
from utils.str import match_after_last_colon
from utils.str import match_story_id


PRODUCT_IMAGES_prefix                = os.getenv('PRODUCT_IMAGES_prefix')
COM_PHOTOS_prefix                    = os.getenv('COM_PHOTOS_prefix')
POST_IMAGES_prefix                   = os.getenv('POST_IMAGES_prefix')
IOEVENT_PRODUCT_IMAGES_CHANGE_prefix = os.getenv('IOEVENT_PRODUCT_IMAGES_CHANGE_prefix')
IOEVENT_COM_PHOTOS_CHANGE_prefix     = os.getenv('IOEVENT_COM_PHOTOS_CHANGE_prefix')
IOEVENT_STORY_PHOTOS_CHANGE_prefix   = os.getenv('IOEVENT_STORY_PHOTOS_CHANGE_prefix')


@mutation.field('docsTags')
def resolve_docsTags(_obj, _info, id, tags):
  res = {}
  doc = None

  changes = 0
  
  # collect added/removed tags
  tags_managed  = []

  try:
    doc = db.session.get(Docs, id)

    if None != doc:
      
      for key, value in tags.items():
        if isinstance(value, bool):
          if value:
            # add tag
            tag_ = Tags.by_name(key, create = True)
            if not tag_ in doc.tags:
              doc.tags.append(tag_)
              tags_managed.append(key)
              changes += 1
          else:
            # remove tag
            tag_ = Tags.by_name(key)
            if (None != tag_) and (tag_ in doc.tags):
              doc.tags.remove(tag_)
              tags_managed.append(key)
              changes += 1
          
          res[key] = value
      
      db.session.commit()

  except Exception as error:
    print(error)
    
  else:
    if 0 < changes:
      io.emit(f'{IOEVENT_DOCS_TAGS_CHANGE_prefix}{doc.id}')
      
      # detect if `@product:images:{pid}`
      # filter tags_managed, @starts_with `@images:product:{pid}`; 
      #  @each io:emit {IOEVENT_PRODUCT_IMAGES_CHANGE_prefix}{pid}
      ioevents_product_images_managed = [
        f'{IOEVENT_PRODUCT_IMAGES_CHANGE_prefix}{match_after_last_colon(name)}' 
          for name in tags_managed 
            if name.startswith(PRODUCT_IMAGES_prefix)
      ]
      for ioevent_ in ioevents_product_images_managed:
        io.emit(ioevent_)

      # detect if `@com:images:{uid}`
      #  filter tags_managed, @starts_with `@com:images:{uid}`; 
      #   @each io:emit @com:images:{uid}
      ioevent_com_photos_managed = [
        f'{IOEVENT_COM_PHOTOS_CHANGE_prefix}{match_after_last_colon(name)}' 
          for name in tags_managed 
            if name.startswith(COM_PHOTOS_prefix)        
      ]      
      for ioevent_ in ioevent_com_photos_managed:
        io.emit(ioevent_)

      # detect if `@story:images:{sid}`
      #  filter tags_managed, @starts_with `@story:com:images:{sid}`;
      #   @each io:emit @story:images:{uid}
      ioevent_story_photos_managed = [
        f'{IOEVENT_STORY_PHOTOS_CHANGE_prefix}{match_story_id(binding)}' 
          for binding in tags_managed 
            if binding.startswith(POST_IMAGES_prefix)
      ]
      for ioevent_ in ioevent_story_photos_managed:
        io.emit(ioevent_)

  return res
