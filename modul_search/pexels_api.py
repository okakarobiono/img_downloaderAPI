import aiohttp

async def search_pexels(query, api_key):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=20"
    headers = {"Authorization": api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return [photo['src']['large2x'] for photo in data['photos']]
    return []