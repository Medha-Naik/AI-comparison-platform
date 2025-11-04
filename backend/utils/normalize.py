import re

def parse_price(price_text):
   
    if not price_text:
        return None
    
    # Remove currency symbols, commas, spaces - keep only digits and decimal point
    clean_text = re.sub(r'[^\d.]', '', price_text)
    
    if not clean_text:
        return None
    
    try:
        # Convert to float first (handles decimals like 66990.00)
        # Then convert to int (removes decimal part: 66990.00 -> 66990)
        price_integer = int(float(clean_text))
        return price_integer
    except (ValueError, TypeError):
        return None