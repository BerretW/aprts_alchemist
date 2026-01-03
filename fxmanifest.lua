fx_version 'cerulean'
lua54 'yes'
rdr3_warning 'I acknowledge that this is a prerelease build of RedM, and I am aware my resources *will* become incompatible once RedM ships.'

author 'SpoiledMouse'
version '1.0'
description 'aprts_alchemist'

games {"rdr3"}
ui_page 'html/index.html'

files {
    'html/index.html',
    'html/style.css',
    'html/script.js',
    'html/img/*.png' -- Pokud budeš chtít obrázky
}

shared_script 'config.lua'
client_script 'client.lua'
server_script 'server.lua'