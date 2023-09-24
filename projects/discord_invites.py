import discord
import asyncio
import time

token = ''
guild_id = 804823279743402054
#logs_channel = 802677487850487851
#bot = commands.Bot(command_prefix='!', intents=intents)

invites = {}
last = ""
intents = discord.Intents.all()
client = discord.Client(intents=intents)


async def fetch():
    global last
    global invites
    await client.wait_until_ready()
    gld = client.get_guild(int(guild_id))
    #logs = client.get_channel(int(logs_channel))
    while True:
        invs = await gld.invites()
        tmp = []
        for i in invs:
            for s in invites:
                if s[0] == i.code:
                    if int(i.uses) > s[1]:
                        usr = gld.get_member(int(last))
                        file = open("discord_data.txt", "r")
                        data = file.read()
                        file.close()
                        data = eval(data)
                        if i.inviter.name not in data.pos():
                            file = open("discord_data.txt", "w")
                            data[i.inviter.name] = [[],0]
                            file.write(str(data))
                            #print(str(data))
                            file.close()
                        if i.inviter.name in data.pos() and time.time() - usr.created_at.timestamp() > 172800:
                            file = open("discord_data.txt", "w")
                            old_data = list(data[i.inviter.name][0])
                            old_data.append(usr.id)
                            data[i.inviter.name][0] = old_data
                            file.write(str(data))
                            file.close()
                            #print(usr.created_at)
                           # testh = f"{usr.name} **joined**; Invited by **{i.inviter.name}** (**{str(len(old_data))}** invites)"
                           # await logs.send(testh)
            tmp.append(tuple((i.code, i.uses)))
        invites = tmp
        await asyncio.sleep(4)


async def check_member_validation():
    await client.wait_until_ready()
    gld = client.get_guild(int(guild_id))

    while True:
        file = open("discord_data.txt", "r+")
        data = file.read()

        if data =='':
            file.write('{}')
        if type(eval(data)) != dict:
            file.write('{}')
        if data !='' or type(eval(data)) == dict :
            data = eval(data)
        file.close()
        for i in data.keys():
            invitee = data[i][0]
            for j in invitee:
                if gld.get_member(j) is not None:
                    pass
                else:
                    old_data = invitee
                    old_data[:] = [x for x in old_data if x != j]
                    data[i][0] = old_data
                    file = open("discord_data.txt", "w")
                    file.write(str(data))
                    file.close()
        await asyncio.sleep(4)

@client.event
async def on_ready():
    print("ready! : Invite Manager")




@client.event
async def on_member_join(meme):
    global last
    last = str(meme.id)
#    print('joined')

def run():
    client.loop.create_task(fetch())
    client.loop.create_task(check_member_validation())
#    client.start(token)
    client.run(token)


if __name__ == '__main__':
    client.loop.create_task(fetch())
    client.loop.create_task(check_member_validation())
    client.run(token)
