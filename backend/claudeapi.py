import anthropic
import os
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    temperature=0,
    system="You are a tasked with generating product ads social media. You are given a product name and a short description of the product. You are to generate 3 ad copies for the product.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please generate the ad copies "
                }
            ]
        },{
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Product Details: name: 'Plushie', description: 'A plushie is a soft, cuddly toy made of fabric or synthetic materials. It is often used as a decorative item or as a gift for children or adults alike.'"
                }
            ]
        }
    ]
)
print(message)