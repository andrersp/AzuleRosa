# -*- coding: utf-8 -*-

from datetime import datetime

from flask import request
from flask_restx import Resource, Namespace

from wraps import required_params

from model.purchase import ModelPurchaseItem, ModelPurchase
from model.provider import ModelProvider
from model.products import ModelProducts
from model.purchase_options import (ModelDeliveryStatus,
                                    ModelPaymentStatus,
                                    ModelPaymentForm,
                                    ModelPaymentMethod)


ns_purchase = Namespace("Purchasing Management",
                        description="Endpoind para gerenciamento de compras")


def to_date(s): return datetime.strptime(s, "%Y-%m-%d")


schema = {
    "id": {"type": "numeric", "required": True, "description": "String vazia para criar um novo ou Inteiro com ID do pedido para editar"},
    "provider_id": {"type": "integer", "required": True, "empty": False, "description": "ID Fornecedor"},
    "value": {"type": "float", "required": True, "empty": False, "description": "Valor total dos produtos"},
    "freight": {"type": "float", "required": True, "empty": False, "description": "Valor do Frete. 0 Se não hoyver"},
    "discount": {"type": "float", "required": True, "empty": False, "description": "Valor do desconto. 0 Se não houver"},
    "total_value": {"type": "float", "required": True, "empty": False, "description": "Valor Total incluindo Frete e/ou Desconto"},
    "delivery_status": {"type": "integer", "required": True, "empty": False, "allowed": [2, 3], "description": "ID estatus entrega: 2 - Em trânsito, 3 - Pendente, "},
    "delivery_time": {"type": "string", "required": True, "empty": False, "description": "Data prevista para entrega"},
    "payment_form": {"type": "integer", "required": True, "empty": False, "allowed": [1, 2, 3], "description": "ID Forma de pagamento. 1 - À Vista, 2 - Depósito Bancário, 3 - A Prazo"},
    "payment_method": {"type": "integer", "required": True, "empty": False, "allowed": [1, 2], "description": "ID Meio de Pagamento: 1 - Dinheiro, 2 - Cartão, 3 - Tranferência Bancaria"},
    "parcel": {"type": "integer", "required": True, "min": 1, "check_with": "payment_method", "description": "Número de parcelas. 1 para pagemento a vista"},
    "obs": {"type": "string", "required": True, "empty": True, "description": "String para observação se houver"},
    "itens": {"type": "list", "required": True, "empty": False, "schema": {
        "type": "dict", "schema": {
            "product_id": {"type": "integer", "required": True, "empty": False, "description": "ID do Produto"},
            "product_name": {"type": "string", "required": False, "empty": True, "description": "Nome do Produto. Opcional. Usado para mensagem caso produto não exista"},
            "unit_price": {"type": "float", "required": True, "empty": False, "description": "Valor de compra unitário"},
            "qtde": {"type": "float", "required": True, "empty": False, "description": "Quantidade"},
            "total_price": {"type": "float", "required": True, "empty": False, "description": "Valor Total dos itens"},
            "obs": {"type": "string", "required": True, "empty": True, "description": "String para observação se houver"}
        }
    }, "description": "List with dictionaries of itens"}

}


@ns_purchase.route("")
class Purchase(Resource):

    def get(self):
        """ Get list of all purchase """

        return {"data": [data.list_purchases() for data in ModelPurchase.query.all()]}, 200

    @required_params(schema)
    @ns_purchase.doc(params=schema)
    def post(self):
        """ Create or update purchase """

        data = request.json

        # Find if purchase exist
        purchase = ModelPurchase.find_purchase(data.get("id"))

        if purchase:
            return self.put()

        provider = ModelProvider.find_provider(data.get("provider_id"))

        if not provider:
            return {"message": "Provider not found"}, 400

        total = []
        for itens in data.get("itens"):

            item = ModelProducts.find_product(itens.get("product_id"))

            if not item:
                return {"message": "Item Not Found", "item": itens}, 400

            if not itens.get("unit_price") * itens.get("qtde") == itens.get("total_price"):
                return {"message": "Total value of item: {} does not check".format(item.name)}, 400

            total.append(itens.get("total_price"))

        if sum(total) != data.get("value"):
            return {"message": "Value does not check"}, 400
        # 11 + 5 - 1

        total_check = sum(total) + data.get("freight") - data.get("discount")

        if total_check != data.get("total_value"):
            return {"message": "total value does not check "}, 400

        try:
            purchase = ModelPurchase(**data)

            for itens in data.get("itens"):
                purchase.itens.append(ModelPurchaseItem(
                    **itens, id_purchase=purchase, provider_id=provider.provider_id))

            purchase.save_purchase()

            return {"message": "purchase saved", "data": purchase.json_purchase()}, 201
        except Exception as err:
            print(err)
            return {"message": "Internal error"}, 500

    # Update Purchase

    @ns_purchase.hide
    def put(self):

        data = request.json
        print(data.get("delivery_time"))

        purchase = ModelPurchase.find_purchase(data.get("id"))

        if not purchase:
            return {"message": "Compra não encontrada"}, 404

        if purchase.delivery_status == 1:
            return {"message": "Compra ja entregue não pode ser alterada"}, 400

        provider = ModelProvider.find_provider(data.get("provider_id"))

        if not provider:
            return {"message": "Provider not found"}, 400

        total = []
        for itens in data.get("itens"):

            item = ModelProducts.find_product(itens.get("product_id"))

            if not item:
                return {"message": "Item Not Found", "item": itens}, 400

            if not itens.get("unit_price") * itens.get("qtde") == itens.get("total_price"):
                return {"message": "Total value of item: {} does not check".format(item.name)}, 400

            total.append(itens.get("total_price"))

        if sum(total) != data.get("value"):
            return {"message": "Value does not check"}, 400
        # 11 + 5 - 1

        total_check = sum(total) + data.get("freight") - data.get("discount")

        if total_check != data.get("total_value"):
            return {"message": "total value does not check "}, 400

        try:
            purchase.update_purchase(**data)

            for itens in data.get("itens"):
                purchase.itens.append(ModelPurchaseItem(
                    **itens, id_purchase=purchase, provider_id=provider.provider_id))

            purchase.save_purchase()

            return {"message": "Compra atualizada", "data": purchase.json_purchase()}, 200
        except Exception as err:
            print(err)
            return {"message": "Internal error"}, 500

        return {"data": data}, 200


schema = {
    "id": {"type": "integer", "required": True, "description": "integer id of purchase"},
    "delivery_status": {"type": "integer", "required": True, "allowed": [1, 2, 3, 4], "description": "integer status of delivery"}
}


@ns_purchase.route("/<int:id_purchase>")
class PurchaseGet(Resource):

    def get(self, id_purchase):
        """ Seleciona compra por ID """

        purchase = ModelPurchase.find_purchase(id_purchase)

        if purchase:
            return {"data": purchase.json_purchase()}, 200

        return {"message": "Purchase not foud"}


@ns_purchase.route("/delivery")
class PurchaseDeliveStatus(Resource):

    @required_params(schema)
    @ns_purchase.doc(params=schema)
    def put(self):
        """ Update Delivery Status """

        data = request.json

        purchase = ModelPurchase.find_purchase(data.get("id"))

        if purchase:

            if data.get("delivery_status") == purchase.delivery_status:
                return {"message": "nothing to change"}, 400

            purchase.update_livery_status(data.get("delivery_status"))
            purchase.save_purchase()

            return {"message": "updated"}

        return {"message": "purchase not found"}, 404