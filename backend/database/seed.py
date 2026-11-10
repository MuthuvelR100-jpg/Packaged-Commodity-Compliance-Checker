from models.category import Category
from models.rule import Rule


DEFAULT_CATEGORIES = (
    ("food", "Food", "Packaged food products."),
    ("cosmetics", "Cosmetics", "Cosmetic products."),
    ("household_products", "Household Products", "Household and cleaning products."),
    ("personal_care", "Personal Care", "Personal care products."),
    ("electronics", "Electronics", "Packaged electronic products."),
    ("clothing", "Clothing", "Packaged clothing products."),
    ("other_packaged_commodities", "Other Packaged Commodities", "Products not covered by another category."),
)

PRELIMINARY_RULES = (
    ("PCM-6-1-B-GENERIC", "other_packaged_commodities", "product_name", "Rule 6(1)(b): common or generic name of the commodity must be declared.", "presence", "standard", True),
    ("PCM-6-1-A-MANUFACTURER", "other_packaged_commodities", "manufacturer_name", "Rule 6(1)(a): manufacturer name and address must be declared.", "presence", "critical", True),
    ("PCM-10-MANUFACTURER-ADDRESS", "other_packaged_commodities", "manufacturer_address", "Rule 10: manufacturer, packer, or importer address must be complete and identifiable.", "presence", "critical", True),
    ("PCM-6-1-C-NET-QUANTITY", "other_packaged_commodities", "net_quantity", "Rule 6(1)(c): net quantity must be declared in a standard unit of weight, measure, or number.", "regex", "critical", True),
    ("PCM-6-1-D-DATE", "other_packaged_commodities", "manufacturing_date", "Rule 6(1)(d): month and year of manufacture, pre-packing, or import must be declared where applicable.", "presence", "standard", True),
    ("PCM-6-1-E-MRP", "other_packaged_commodities", "mrp", "Rule 6(1)(e): retail sale price must be declared.", "regex", "critical", True),
    ("PCM-6-2-CONSUMER-CARE", "other_packaged_commodities", "consumer_care_phone", "Rule 6(2): telephone number of the consumer complaint contact must be declared.", "regex", "standard", True),
    ("PCM-6-2-CONSUMER-EMAIL", "other_packaged_commodities", "consumer_care_email", "Rule 6(2): email address of the consumer complaint contact, if available, may be declared.", "regex", "standard", True),
    ("PCM-12-13-QUANTITY-UNIT", "household_products", "net_quantity", "Rules 12–13: quantity must use the applicable permitted unit of weight, measure, or number.", "regex", "critical", True),
    ("PCM-14-CLOTHING-DIMENSIONS", "clothing", "product_name", "Rule 14: number and finished dimensions apply to specified textile commodities.", "presence", "standard", True),
    ("PCM-6-1-F-DIMENSIONS", "electronics", "product_name", "Rule 6(1)(f): dimensions must be declared where the size of the commodity is relevant.", "presence", "standard", True),
    ("PCM-5-SECOND-SCHEDULE", "food", "net_quantity", "Rule 5 and Second Schedule: listed commodities may be subject to specified standard pack quantities.", "presence", "standard", False),
    ("PCM-6-1-A-FOOD-EXCEPTION", "food", "manufacturer_name", "Rule 6(1)(a) notes a food-article exception; verify the applicable food law before validation.", "presence", "standard", False),
    ("PCM-6-1-D-COSMETICS-EXCEPTION", "cosmetics", "manufacturing_date", "Rule 6(1)(d) notes a cosmetics exception; verify the Drugs and Cosmetics Rules before validation.", "presence", "standard", False),
)

VALIDATION_EXPRESSIONS = {
    "net_quantity": r"\s*[0-9]+(?:[.,][0-9]+)?\s*(?:g|kg|ml|l|cm|m|mm|sq\.?\s*m|no\.?|n|u)\s*",
    "mrp": r"\s*[₹]?\s*[0-9]+(?:[.,][0-9]{1,2})?\s*",
    "consumer_care_phone": r"\s*\+?[0-9][0-9\s().-]{7,}\s*",
    "consumer_care_email": r"\s*[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\s*",
}


def seed_categories(db) -> None:
    for code, name, description in DEFAULT_CATEGORIES:
        if not Category.query.filter_by(code=code).first():
            db.session.add(Category(code=code, name=name, description=description))
    db.session.commit()


def seed_preliminary_rules(db) -> None:
    for rule_code, category, field_name, description, validation_type, severity, active in PRELIMINARY_RULES:
        if not Rule.query.filter_by(rule_code=rule_code).first():
            db.session.add(Rule(
                rule_code=rule_code,
                category=category,
                field_name=field_name,
                requirement_description=description,
                mandatory=True,
                validation_type=validation_type,
                validation_expression=VALIDATION_EXPRESSIONS.get(field_name),
                severity=severity,
                source_reference="Rules 2011.pdf, Legal Metrology (Packaged Commodities) Rules, 2011",
                rule_version="2011-preliminary",
                active=active,
            ))
    db.session.commit()
