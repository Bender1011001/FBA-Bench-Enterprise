from fba_bench.money import Money
from models.product import Product


def test_product_accepts_money_price_and_cost():
    p = Product(
        {"id": "ASIN1", "price": Money(1999, "USD"), "cost": Money(1000, "USD")}
    )
    assert isinstance(p.price, Money)
    assert p.price.cents == 1999
    assert p.cost.cents == 1000


def test_product_accepts_numeric_price_and_cost():
    p = Product({"id": "ASIN2", "price": 29.99, "cost": 15.0})
    assert isinstance(p.price, Money)
    assert p.price.cents == 2999
    assert p.cost.cents == 1500


def test_product_to_dict_preserves_money_objects():
    p = Product({"id": "ASIN3", "price": 9.5, "cost": 4.0})
    d = p.to_dict()
    assert d["price"].cents == p.price.cents
    assert d["cost"].cents == p.cost.cents
