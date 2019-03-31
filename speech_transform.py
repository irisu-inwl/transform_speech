import json
import transform_rule.py

def lambda_handler(event, context):
    tr = Transform_Rule()
    speech = event['speech']
    text = tr.fit_rule_table(speech)
    return {
        'text': text
    }