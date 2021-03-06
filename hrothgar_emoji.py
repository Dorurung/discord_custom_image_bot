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
import hashlib
import asyncio
from collections import defaultdict

client = discord.Client()

keyword_id={}
id_image={}
blacklist = defaultdict(lambda: [])
blacklistall = []

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

ffxiv = ['nsfw']
debu = ['?????? ??????', '??????-?????? ??????']

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
    if reaction.message.channel.name != '????????????':
        print(reaction.emoji)
        if reaction.emoji == '???':
            if reaction.count == 3:
                e = discord.Embed(description=f'{reaction.message.content}\n\n{reaction.message.channel.name}?????? {str(reaction.message.created_at)}??? ??????')
                e.set_author(name=reaction.message.author.name, icon_url=reaction.message.author.avatar_url)
                archive = discord.utils.get(reaction.message.guild.channels, name='????????????')
                await archive.send(embed=e)

@client.event
async def on_message(message):
    if message.author == client.user:
    	return

    if message.content in keyword_id.keys() and not message.content in blacklist[message.author] and not message.author in blacklistall:
        image_name = id_image[keyword_id[message.content]]
        image_url = 'image/' + image_name
        extension = '.' + image_name.split('.')[-1]
        files = discord.File(image_url, filename=f'image{extension}')
        e = discord.Embed(description=f'{message.content}')
        e.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        e.set_image(url=f'attachment://image{extension}')
        await message.channel.send(embed=e, file=files)
        await message.delete()
    
    if message.content.startswith('!???????????????') or message.content.startswith('!???????????????'):
        _, keyword = message.content.split(' ')
        if keyword in id_image.keys():
            await message.channel.send('?????? ?????? ?????????ID???! ?????? ???????????? ???????????? ????????? ```!??????????????? ?????????ID```')
            return
        e, files = add_image(message, keyword)
        await message.channel.send('????????? ?????? ?????????!', embed=e, file=files)

    if message.content.startswith('!???????????????') or message.content.startswith('!???????????????'):
        _, keyword, ids = message.content.split(' ')
        if ids in id_image.keys():
            keyword_id[keyword] = ids
            save_dicts()
            await message.channel.send('????????? ?????? ?????????!')
        else:
            await message.channel.send('?????? ?????????ID???!')
    
    if message.content.startswith('!???????????????'):
        _, keyword = message.content.split(' ')
        try:
            del keyword_id[keyword]
            save_dicts()
            await message.channel.send('????????? ?????? ?????????!')
        except KeyError:
            await message.channel.send('?????? ????????????!')
    
    if message.content.startswith('!?????????????????????ID??????'):
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
            await message.channel.send(f'{ids}???(???) {keyword}??? ????????????!', embed=e, file=files)
        except KeyError:
            await message.channel.send('?????? ????????????!')
    
    if message.content.startswith('!???????????????'):
        await message.channel.send(file=discord.File('keyword_id.txt'))

    if message.content.startswith('!???????????????'):
        await message.channel.send(file=discord.File('id_image.txt'))

    if message.content.startswith('!??????!'):
        with open('help.txt', 'r', encoding='utf-8') as f:
            helps = f.read()
        await message.channel.send(helps)
    
    if message.content.startswith('!???????????????'):
        _, ids = message.content.split(' ')
        if ids in id_image.keys():
            e, files = add_image(message, ids)
            await message.channel.send('????????? ?????? ?????????!', embed=e, file=files)
        else:
            await message.channel.send('?????? ?????????ID???!')
    
    if message.content.startswith('!??????????????????'):
        blacklistall.remove(message.author)
        await message.channel.send(f'{message.author}??? ??????????????? ??? ??? ?????? ?????????!')
    
    elif message.content.startswith('!????????????'):
        blacklistall.append(message.author)
        await message.channel.send(f'{message.author}??? ??????????????? ??? ??? ?????? ?????????!')

    if message.content.startswith('!?????????????????????') or message.content.startswith('!?????????????????????'):
        array = message.content.split(' ')[1:]
        blacklist[message.author].extend(array)
        save_dicts()
        await message.channel.send('??????????????? ???????????????!')
    
    if message.content.startswith('!?????????????????????'):
        array = message.content.split(' ')[1:]
        blacklist[message.author] = list(set(blacklist[message.author]) - set(array))
        save_dicts()
        await message.channel.send('??????????????? ???????????????!')
    
    if message.content.startswith('!????????????'):
        filelist = os.listdir('nsfw')
        image_url = 'nsfw/' + filelist[random.randrange(0, len(filelist))]
        await message.channel.send(file=discord.File(image_url))

    if message.content.startswith('!????????????'):
        filelist = os.listdir('debu')
        image_url = 'debu/' + filelist[random.randrange(0, len(filelist))]
        await message.channel.send(file=discord.File(image_url))

    if (message.channel.name in ffxiv or str(message.channel.category) in debu) and message.author != '????????????':
        if message.channel.name in ffxiv:
            savedir = 'nsfw'
        elif str(message.channel.category) in debu:
            savedir = 'debu'
        try:
            for i in message.attachments:
                r = requests.get(i.url, stream=True)
                extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                filenum = len(os.listdir(savedir))
                with open(f'{savedir}/{filenum}{extension}', 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                await message.add_reaction('???')
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
                    filenum = len(os.listdir(savedir))
                    with open(f'{savedir}/{filenum}{extension}', 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            except:
                url = lookup[0].entities['media'][0]['media_url']
                r = requests.get(url, stream=True)
                extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                filenum = len(os.listdir(savedir))
                with open(f'{savedir}/{filenum}{extension}', 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            await message.add_reaction('???')
    
    if message.content.startswith('!??????'):
        _, name1, name2 = message.content.split(' ')

        name1 = '**' + name1 + '**'
        name2 = '**' + name2 + '**'

        seed = (hashlib.md5(name1.encode()).hexdigest(), hashlib.md5(name2.encode()).hexdigest())
        stat = [{}, {}]
        for i, s in enumerate(stat):
            s['atk'] = int(seed[i][:2], 16) 
            s['def'] = int(seed[i][2:4], 16)
            s['hit'] = int(seed[i][4:6], 16)
            s['agi'] = int(seed[i][6:8], 16)
            s['maxhp'] = int(int(seed[i][8:11], 16) / 4) + 128
            s['hp'] = s['maxhp']
        
        def hpbar(stat, name1, name2):
            p1percent = int(stat[0]['hp'] / stat[0]['maxhp'] * 10 + 0.99)
            p1box = '???'*min((10-p1percent), 10) + '???'*p1percent
            p2percent = int(stat[1]['hp'] / stat[1]['maxhp'] * 10 + 0.99)
            p2box = '???'*p2percent + '???'*min((10-p2percent), 10) 
            return f'\n[{name1}]{p1box}vs{p2box}[{name2}]'

        def sigmoid(x):
            return 1 / (1 +np.exp(-x))

        sendmessage = await message.channel.send(f'''{name1}??? {name2}??? ??????!
{name1}) ATK: {stat[0]['atk']}, DEF: {stat[0]['def']}, HIT: {stat[0]['hit']}, AGI: {stat[0]['agi']}, HP: {stat[0]['hp']}
{name2}) ATK: {stat[1]['atk']}, DEF: {stat[1]['def']}, HIT: {stat[1]['hit']}, AGI: {stat[1]['agi']}, HP: {stat[1]['hp']}
[{name1}]->[{name2}] ?????????: {int(sigmoid((stat[0]['hit'] - stat[1]['agi'])/128)*100)}%, ?????????: {int(sigmoid((stat[0]['atk'] - stat[1]['def'])/128)*512)}~{int(sigmoid((stat[0]['atk'] - stat[1]['def'])/128)*512)+64}
[{name2}]->[{name1}] ?????????: {int(sigmoid((stat[1]['hit'] - stat[0]['agi'])/128)*100)}%, ?????????: {int(sigmoid((stat[1]['atk'] - stat[0]['def'])/128)*512)}~{int(sigmoid((stat[1]['atk'] - stat[0]['def'])/128)*512)+64}
{name1 if stat[0]['agi'] > stat[1]['agi'] else name2}??? ??????''')
        

        name1turn = True if stat[0]['agi'] > stat[1]['agi'] else False
        final_string = sendmessage.content
        while stat[0]['hp'] > 0 and stat[1]['hp'] > 0:
            if name1turn:
                hit_percent = sigmoid((stat[0]['hit'] - stat[1]['agi'])/128)
                if random.random() <= hit_percent:
                    dmg = int(sigmoid((stat[0]['atk'] - stat[1]['def'])/128)*512) + random.randrange(0, 64)
                    string = f'\n[{name1}]??? ??????! [{name2}]??? {dmg}??? ????????? ?????????!'
                    stat[1]['hp'] -= dmg
                else:
                    string = f'\n[{name1}]??? ??????! [{name2}]??? ????????? ????????????!'
                name1turn = False
            else:
                hit_percent = sigmoid((stat[1]['hit'] - stat[0]['agi'])/128)
                if random.random() <= hit_percent:
                    dmg = int(sigmoid((stat[1]['atk'] - stat[0]['def'])/128)*512) + random.randrange(0, 64)
                    string = f'\n[{name2}]??? ??????! [{name1}]??? {dmg}??? ????????? ?????????!'
                    stat[0]['hp'] -= dmg
                else:
                    string = f'\n[{name2}]??? ??????! [{name1}]??? ????????? ????????????!'
                name1turn = True
            final_string = final_string + string
            await sendmessage.edit(content=final_string+hpbar(stat, name1, name2))
            await asyncio.sleep(2)
        if stat[1]['hp'] < 0:
            string = f'\n[{name2}]??? ????????????. [{name1}]??? ??????!'
        else:
            string = f'\n[{name1}]??? ????????????. [{name2}]??? ??????!'
        final_string = final_string + string
        await sendmessage.edit(content=final_string+hpbar(stat, name1, name2))

'''
@client.event
async def on_message_edit(before, message):
    print('changed')
    if message.channel.name == 'nsfw' and message.author != '????????????':
        print('nsfw! changed')
        try:
            for embed in message.embeds:
                r = requests.get(embed.image.url, stream=True)
                extension = mimetypes.guess_extension(r.headers.get('content-type', '').split(';')[0])
                filenum = len(os.listdir('nsfw'))
                with open(f'nsfw/{filenum}{extension}', 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            await message.add_reaction('???')
        except:
            pass
'''

client.run(token)