# -*- coding: utf-8 -*-

from base64 import b64decode
import os
import imghdr
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required

from wraps import required_params

from model.products import ModelProducts
from model.products_image import ModelImagesProducts

product_space = Namespace("Products", description="Resources for Produtos")

schema = {
    "id": {"type": "numeric", "required": True, "description": "numeric string value or int"},
    "name": {"type": "string", "required": True, "empty": False, "description": "name of product"},
    "category": {"type": "integer", "required": True, "description": "integer value of category"},
    "brand": {"type": "integer", "required": True, "description": "integer valur of brand"},
    "minimum_stock": {"type": "float", "required": True, "description": "float value of minimum stock"},
    "maximum_stock": {"type": "float", "required": True, "description": "float value of maximum stock"},
    "long_description": {"type": "string", "required": True, "empty": True, "description": "Long Description of product"},
    "short_description": {"type": "string", "required": True, "empty": False, "description": "Short Description of product, max 200", "maxlength": 200},
    "sale_price": {"type": "float", "required": True, "description": "value of sale price of product"},
    "available": {"type": "boolean", "required": True, "description": "if product is unavailable for sale"},
    "height": {"type": "float", "required": True, "description": "product height for shipping"},
    "widht": {"type": "float", "required": True, "description": "product widht for shipping"},
    "length": {"type": "float", "required": True, "description": "product length for shipping"},
    "weight": {"type": "float", "required": True, "description": "product weight for shipping"},
    "maximum_discount": {"type": "float", "required": True, "description": "maximum_discount for this product"},
    "images": {"type": "list", "schema": {"type": "string"}, "required": True, "empty": True}
}


# Function to converte base64 image to file

def upload_image(image):

    image = b64decode(image)
    extension = imghdr.what(None, h=image)
    filename = str(datetime.now().timestamp()) + "." + extension

    with open(os.path.join("static/images/" + filename), "wb") as file_to_save:
        file_to_save.write(image)

    return filename


@product_space.route("")
class ProductsGet(Resource):
    # @jwt_required
    def get(self):
        """ Get all products enabled in Stock """
        return {"data": [product.list_product() for product in ModelProducts.query.all()]}

    @required_params(schema)
    @product_space.doc(params=schema)
    def post(self):
        """ Create or Update product.
        For create a new product send a empty string value or send a int id product value for update """

        data = request.json

        product = ModelProducts.find_product(data.get("id"))

        if product:
            return self.put()

        try:

            product = ModelProducts(**data)

            for images in data.get("images"):
                product.images.append(ModelImagesProducts(
                    upload_image(images), product))
            product.save_product()

            return {"message": "product created", "data": product.list_product()}, 201
        except Exception as err:
            print(err)
            return {"message": "Internal error"}, 500

        return {"messa": "ok"}, 200

    @product_space.hide
    def put(self):
        data = request.json
        product = ModelProducts.find_product(data.get("id"))

        try:
            product.update_product(**data)
            product.save_product()
            return {"message": "product updated", "data": product.list_product()}
        except:
            return {"message": "internal error"}, 500


@product_space.route("/<int:id_product>")
class ProductGet(Resource):

    def get(self, id_product):
        """ Get Product by id """

        product = ModelProducts.find_product(id_product)

        if product:
            return {"data": product.list_product()}, 200

        return {"message": "product not found"}, 404

    # def get(self, id_product):
    #     """ Get Product by id """

    #     product = ModelProducts.find_product(id_product)

    #     if product:
    #         return {"data": product.list_product()}, 200

    #     return {"message": "product not found"}, 404