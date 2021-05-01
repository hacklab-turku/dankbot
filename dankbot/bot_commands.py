from chat_functions import send_text_to_room
import aiohttp
import json


class Command(object):
    def __init__(self, client, store, config, command, room, event):
        """A command made by a user

        Args:
            client (nio.AsyncClient): The client to communicate to matrix with
            store (Storage): Bot storage
            config (Config): Bot configuration parameters
            command (str): The command and arguments
            room (nio.rooms.MatrixRoom): The room the command was sent in
            event (nio.events.room_events.RoomMessageText): The event describing the command
        """
        self.client = client
        self.store = store
        self.config = config
        self.command = command
        self.room = room
        self.event = event
        self.args = self.command.split()[1:]

    async def process(self):
        """Process the command"""
        if self.command.startswith("echo"):
            await self._echo()
        elif self.command.startswith("help"):
            await self._show_help()
        elif self.command.startswith("invite"):
            await self._invite()
        elif self.command.startswith("lab"):
            await self._lab()
        else:
            await self._unknown_command()

    async def _echo(self):
        """Echo back the command's arguments"""
        response = " ".join(self.args)
        await send_text_to_room(self.client, self.room.room_id, response)

    async def _invite(self):
        if not self.args:
            text = (
                "You did not give me an invite."
            )
            await send_text_to_room(self.client, self.room.room_id, text)

        try:
            if self.args[0] == "join":
                await self.client.join(self.args[1])
                text = "Successfully joined given room."
            elif self.args[0] == "leave":
                await self.client.room_leave(self.room.room_id)
        except Exception as e:
            text = f"Joining to room failed, {e}"
            await send_text_to_room(self.client, self.room.room_id, text)

    async def _lab(self):
        try:
            topic = self.args[0]
            if topic == "light":
                msg = await self._lab_light()
                await send_text_to_room(self.client, self.room.room_id, msg)
            elif topic == "wifi":
                msg = await self._lab_wifi()
                await send_text_to_room(self.client, self.room.room_id, msg)
            else:
                first_msg = "You did not specify which information you want, so I'm gonna guess it as both."
                await send_text_to_room(self.client, self.room.room_id, first_msg)
                light_msg = await self._lab_light()
                await send_text_to_room(self.client, self.room.room_id, light_msg)
                wifi_msg = await self._lab_wifi()
                await send_text_to_room(self.client, self.room.room_id, wifi_msg)
        except IndexError:
            pass


    async def _lab_light(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost/pi_api/gpio/?a=readPin&pin=1") as response:
                api_response = await response.json()
                api_data = api_response['data']
                if api_data == 0:
                    msg = "Someone is probably at the lab as the light is on."
                else:
                    msg = "Nobody is at the lab, the light is currently off."
                return msg

    async def _lab_wifi(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost/visitors/api/v1/visitors.php?format=json") as response:
                api_response = await response.json()
                if not api_response:
                    msg = "Nobody is using the Wifi that I know of currently."
                else:
                    msg = "Someone or multiple someones are using the Wifi at the lab currently."
                return msg

    async def _show_help(self):
        """Show the help text"""
        if not self.args:
            text = (
                "Hello, I am a bot made with matrix-nio! Use `help commands` to view "
                "available commands."
            )
            await send_text_to_room(self.client, self.room.room_id, text)
            return

        topic = self.args[0]
        if topic == "commands":
            text = "Available commands"
            text += "lab - Outputs the current lab occupancy information"
        else:
            text = "Unknown help topic!"
        await send_text_to_room(self.client, self.room.room_id, text)

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            f"Unknown command '{self.command}'. Try the 'help' command for more information.",
        )
