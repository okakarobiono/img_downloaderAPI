import aiohttp

async def search_pixabay(query, api_key):
    url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=photo&per_page=20"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return [hit['largeImageURL'] for hit in data['hits']]
    return []