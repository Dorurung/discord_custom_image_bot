# -*- conding: utf-8 -*-
import discord
import requests
import shutil
import cv2
import numpy as np
import mimetypes
import os
import random
import tweepy
import re
from collections import defaultdict

client = discord.Client()

keyword_id={}
id_image={}
blacklist = defaultdict(lambda: [])

with open('tokens.txt', 'r') as f:
    exec(f.read())

auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret_key)
auth.set_access_token(twitter_access_token, twitter_access_token_secret)
twitter_api = tweepy.API(auth)

def load_dicts():
    with open('keyword_id.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            keyword, ids = line.strip().split(' ')
            keyword_id[keyword] = ids
    with open('id_image.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            ids, image = line.strip().split(' ')
            id_image[ids] = image
    with open('blacklist.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            array = line.strip().split(' ')
            blacklist[array[0]] = array[1:]

def save_dicts():
    with open('keyword_id.txt', 'w', encoding='utf-8') as f:
        for key in keyword_id.keys():
            f.write(f'{key} {keyword_id[key]}\n')
    with open('id_image.txt', 'w', encoding='utf-8') as f:
        for key in id_image.keys():
            f.write(f'{key} {id_image[key]}\n')
    with open('blacklist.txt', 'w', encoding='utf-8') as f:
        for key in blacklist.keys():
            f.write(f'{key} {" ".join(blacklist[key])}\n')

def add_image(message, keyword):
    r = requests.get(message.attachments[0].url, stream=True)
    extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
    if keyword in id_image.keys():
        number = id_image[keyword][:-4]
    else:
        number = str(len(id_image.keys()))
    with open(f'image/{number}{extension}', 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    if extension != '.gif':
        img_array = np.fromfile(f'image/{number}{extension}', np.uint8)
        src = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        origin_height, origin_width = src.shape[:2]
        if origin_height > origin_width:
            pillar = int((origin_height-origin_width)/2)
            dst = src[pillar:origin_height-pillar,:].copy()
        #elif origin_height < origin_width:
        #    pillar = int((origin_width-origin_height)/2)
        #    dst = src[:,pillar:origin_width-pillar].copy()
        else:
            dst = src.copy()
        height, width = dst.shape[:2]
        if height > 128:
            dst2 = cv2.resize(dst, dsize=(int(128/height*width), 128), interpolation=cv2.INTER_AREA)
        else:
            dst2 = dst.copy()
        result, encoded_img = cv2.imencode(extension, dst2)
        if result:
            with open(f'image/{number}{extension}', mode='w+b') as f:
                encoded_img.tofile(f)
    keyword_id[keyword] = keyword
    id_image[keyword] = f'{number}{extension}'
    save_dicts()
    image_url = 'image/' + f'{number}{extension}'
    files = discord.File(image_url, filename=f'image{extension}')
    e = discord.Embed()
    e.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    e.set_image(url=f'attachment://image{extension}')
    return e, files

archive = ''

@client.event
async def on_ready():
    global archive
    print('We have logged in as {0.user}'.format(client))
    load_dicts()
    archive = client.get_channel(836914774973218847)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    if reaction.message.channel.name != '아카이브':
        if reaction.emoji.name == 'timberwolf36':
            if reaction.count == 1:
                e = discord.Embed(description=f'{reaction.message.content}\n\n{reaction.message.channel.name}에서 {str(reaction.message.created_at)}에 보냄')
                e.set_author(name=reaction.message.author.name, icon_url=reaction.message.author.avatar_url)
                await archive.send(embed=e)

@client.event
async def on_message(message):
    if message.author == client.user:
    	return

    if message.content in keyword_id.keys() and not message.content in blacklist[message.author]:
        image_name = id_image[keyword_id[message.content]]
        image_url = 'image/' + image_name
        extension = '.' + image_name.split('.')[-1]
        files = discord.File(image_url, filename=f'image{extension}')
        e = discord.Embed(description=f'{message.content}')
        e.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        e.set_image(url=f'attachment://image{extension}')
        await message.channel.send(embed=e, file=files)
        await message.delete()
    
    if message.content.startswith('!이미지추가') or message.content.startswith('!이미지등록'):
        _, keyword = message.content.split(' ')
        if keyword in id_image.keys():
            await message.channel.send('이미 있는 이미지ID야! 기존 이미지를 수정하고 싶으면 ```!이미지수정 이미지ID```')
            return
        e, files = add_image(message, keyword)
        await message.channel.send('이미지 추가 했어잉!', embed=e, file=files)

    if message.content.startswith('!키워드추가') or message.content.startswith('!키워드등록'):
        _, keyword, ids = message.content.split(' ')
        if ids in id_image.keys():
            keyword_id[keyword] = ids
            save_dicts()
            await message.channel.send('키워드 추가 했어잉!')
        else:
            await message.channel.send('없는 이미지ID래!')
    
    if message.content.startswith('!키워드삭제'):
        _, keyword = message.content.split(' ')
        try:
            del keyword_id[keyword]
            save_dicts()
            await message.channel.send('키워드 삭제 했어잉!')
        except KeyError:
            await message.channel.send('없는 키워드래!')
    
    if message.content.startswith('!키워드로이미지ID확인'):
        _, keyword = message.content.split(' ')
        try:
            ids = keyword_id[keyword]
            image_name = id_image[keyword_id[message.content]]
            image_url = 'image/' + image_name
            extension = '.' + image_name.split('.')[-1]
            files = discord.File(image_url, filename=f'image{extension}')
            e = discord.Embed()
            e.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            e.set_image(url=f'attachment://image{extension}')
            await message.channel.send(f'{ids}이(가) {keyword}의 이미지야!', embed=e, file=files)
        except KeyError:
            await message.channel.send('없는 키워드래!')
    
    if message.content.startswith('!키워드목록'):
        await message.channel.send(file=discord.File('keyword_id.txt'))

    if message.content.startswith('!이미지목록'):
        await message.channel.send(file=discord.File('id_image.txt'))

    if message.content.startswith('!도움!'):
        with open('help.txt', 'r', encoding='utf-8') as f:
            helps = f.read()
        await message.channel.send(helps)
    
    if message.content.startswith('!이미지수정'):
        _, ids = message.content.split(' ')
        if ids in id_image.keys():
            e, files = add_image(message, ids)
            await message.channel.send('이미지 수정 했어잉!', embed=e, file=files)
        else:
            await message.channel.send('없는 이미지ID래!')
    
    if message.content.startswith('!블랙리스트등록') or message.content.startswith('!블랙리스트추가'):
        array = message.content.split(' ')[1:]
        blacklist[message.author].extend(array)
        save_dicts()
        await message.channel.send('블랙리스트 추가했어잉!')
    
    if message.content.startswith('!블랙리스트삭제'):
        array = message.content.split(' ')[1:]
        blacklist[message.author] = list(set(blacklist[message.author]) - set(array))
        save_dicts()
        await message.channel.send('블랙리스트 삭제했어잉!')
    
    if message.content.startswith('!랜덤야짤'):
        filelist = os.listdir('nsfw')
        image_url = 'nsfw/' + filelist[random.randrange(0, len(filelist))]
        await message.channel.send(file=discord.File(image_url))

    if message.channel.name == 'nsfw' and message.author != '미니쿠다':
        try:
            r = requests.get(message.attachments[0].url, stream=True)
            extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
            filenum = len(os.listdir('nsfw'))
            with open(f'nsfw/{filenum}{extension}', 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            await message.add_reaction('✅')
        except:
            pass
        if 'https://twitter.com/' in message.content:
            p = re.compile(r'https:\/\/twitter.com\/.+\/(\d+)')
            ids = p.search(message.content).group(1)
            lookup = twitter_api.statuses_lookup([ids])
            try:
                for media in lookup[0].extended_entities['media']:
                    url = media['media_url']
                    r = requests.get(url, stream=True)
                    extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                    filenum = len(os.listdir('nsfw'))
                    with open(f'nsfw/{filenum}{extension}', 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            except:
                url = lookup[0].entities['media'][0]['media_url']
                r = requests.get(url, stream=True)
                extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                filenum = len(os.listdir('nsfw'))
                with open(f'nsfw/{filenum}{extension}', 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            await message.add_reaction('✅')
'''
@client.event
async def on_message_edit(before, message):
    print('changed')
    if message.channel.name == 'nsfw' and message.author != '미니쿠다':
        print('nsfw! changed')
        try:
            for embed in message.embeds:
                r = requests.get(embed.image.url, stream=True)
                extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                filenum = len(os.listdir('nsfw'))
                with open(f'nsfw/{filenum}{extension}', 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            await message.add_reaction('✅')
        except:
            pass
'''

client.run(token)