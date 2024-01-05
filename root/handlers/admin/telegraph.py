from aiograph import Telegraph


async def photo_link_aiograph(photo):
    telegraph = Telegraph()
    links = await telegraph.upload(photo)
    await telegraph.close()
    return links[0]
