import aiohttp

async def search_bing(query, subscription_key, max_images=50):
    url = f"https://api.bing.microsoft.com/v7.0/images/search?q={query}&count={max_images}"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return [img['contentUrl'] for img in data['value']]
    return []