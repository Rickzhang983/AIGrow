factors =  {'nutrient_EC': 1.6, 'nutrient_PH': 6.7}
import re
for factor_name, facotr_range in factors.items():
    facotr_range = str(facotr_range)
    factor_values = re.findall('[0-9]+[.]?[0-9]*', facotr_range)
    print('factor values', factor_values)

