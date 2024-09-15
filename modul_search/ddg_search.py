import asyncio
from fastbook import search_images_ddg
import logging

async def async_search_images_ddg(query, max_images=150):
    try:
        # Ensure max_images is always an integer
        max_images = 100 if max_images is None else int(max_images)
        result = await asyncio.to_thread(search_images_ddg, query, max_images)
        if result is None:
            logging.warning(f"search_images_ddg returned None for query: {query}")
            return []
        return result
    except Exception as e:
        logging.error(f"Error in async_search_images_ddg: {str(e)}")
        logging.error(f"Query: {query}, Max images: {max_images}")
        return []