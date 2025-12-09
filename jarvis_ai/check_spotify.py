import tools
import config

def check_media_players():
    print("Searching for Media Players...")
    # Search for "media_player" to see all players
    print(tools.search_ha_entities("media_player"))
    # Search specifically for spotify
    print(tools.search_ha_entities("spotify"))

if __name__ == "__main__":
    check_media_players()
