#!/usr/bin/env python3
import asyncio
import hashlib
import os
import sys
import aiohttp
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    env_paths = [
        Path(__file__).parent.parent.parent / '.env',
        Path('/root/shop-bot/.env'),
        Path('/app/../.env'),
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

from db.methods import get_vpn_users, engine
from db.models import VPNUsers
from sqlalchemy import update
import glv

try:
    from db.methods import update_vpn_id
except ImportError:
    async def update_vpn_id(tg_id: int, vpn_id: str):
        async with engine.connect() as conn:
            sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(vpn_id=vpn_id)
            await conn.execute(sql_q)
            await conn.commit()

async def get_remnawave_users(panel_host: str, token: str):
    headers = {
        'X-Forwarded-For': '127.0.0.1',
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Host': panel_host,
        'X-Real-IP': '127.0.0.1',
        'Authorization': f"Bearer {token}"
    }
    api_base_url = f"{panel_host}/api"
    
    timeout = aiohttp.ClientTimeout(total=300.0)
    all_users = []
    
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        try:
            url = f"{api_base_url}/users"
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                if 'response' not in data:
                    print("Неожиданный формат ответа API")
                    print(f"Ответ: {data}")
                    return []
                
                response_data = data['response']
                users = response_data.get('users', [])
                total = response_data.get('total', len(users))
                
                print(f"Первая страница: получено {len(users)} пользователей, всего: {total}")
                
                all_users.extend(users)
                
                if total and len(users) < total:
                    print(f"ВНИМАНИЕ: API вернул только {len(users)} из {total} пользователей")
                    print("Получение всех пользователей через пагинацию (start/size)...")
                    
                    page_size = 100
                    start = len(users)
                    
                    while len(all_users) < total:
                        paginated_url = f"{api_base_url}/users?start={start}&size={page_size}"
                        print(f"  Запрос: start={start}, size={page_size}")
                        
                        async with session.get(paginated_url) as paginated_response:
                            paginated_response.raise_for_status()
                            paginated_data = await paginated_response.json()
                            
                            if 'response' not in paginated_data:
                                print(f"  Неожиданный формат ответа на странице")
                                break
                            
                            paginated_response_data = paginated_data['response']
                            paginated_users = paginated_response_data.get('users', [])
                            
                            if not paginated_users:
                                print(f"  Больше нет пользователей")
                                break
                            
                            all_users.extend(paginated_users)
                            start += len(paginated_users)
                            
                            print(f"  Загружено {len(all_users)} из {total} пользователей...")
                            
                            if len(all_users) >= total:
                                print(f"  Достигнуто общее количество пользователей")
                                break
                            
                            if len(paginated_users) < page_size:
                                print(f"  Получено меньше size, значит это последняя страница")
                                break
            
            print(f"Итого получено: {len(all_users)} пользователей")
            return all_users
        except Exception as e:
            print(f"Ошибка при получении пользователей из Remnawave: {e}")
            import traceback
            traceback.print_exc()
            if all_users:
                print(f"Получено частично: {len(all_users)} пользователей")
                return all_users
            return []

def is_md5_hash(s: str) -> bool:
    if len(s) != 32:
        return False
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

async def sync_vpn_ids():
    print("Начало синхронизации vpn_id...")
    print(f"Время: {datetime.now()}")
    print()
    
    panel_host = glv.config.get('PANEL_HOST')
    token = glv.config.get('REMNAWAVE_TOKEN')
    
    if not panel_host or not token:
        print("Ошибка: PANEL_HOST или REMNAWAVE_TOKEN не установлены")
        return
    
    print("Получение пользователей из Remnawave...")
    remnawave_users = await get_remnawave_users(panel_host, token)
    print(f"Найдено пользователей в Remnawave: {len(remnawave_users)}")
    print()
    
    print("Получение пользователей из БД бота...")
    bot_users = await get_vpn_users()
    print(f"Найдено пользователей в БД бота: {len(bot_users)}")
    print()
    
    updated = 0
    not_found = 0
    already_correct = 0
    
    print("Синхронизация...")
    print()
    
    remnawave_username_to_user = {user['username']: user for user in remnawave_users}
    
    print("Примеры username из Remnawave (первые 5):")
    for i, username in enumerate(list(remnawave_username_to_user.keys())[:5]):
        is_md5 = "MD5" if is_md5_hash(username) else "не MD5"
        print(f"  {i+1}. {username} ({is_md5})")
    print()
    
    print("Поиск соответствий...")
    print()
    
    tg_id_to_bot_user = {user.tg_id: user for user in bot_users}
    vpn_id_to_bot_user = {user.vpn_id: user for user in bot_users}
    processed_tg_ids = set()
    remnawave_not_in_bot = []
    
    for remnawave_username in remnawave_username_to_user.keys():
        found_match = False
        
        if remnawave_username in vpn_id_to_bot_user:
            bot_user = vpn_id_to_bot_user[remnawave_username]
            if bot_user.tg_id not in processed_tg_ids:
                already_correct += 1
                processed_tg_ids.add(bot_user.tg_id)
                found_match = True
                continue
        
        if is_md5_hash(remnawave_username):
            for bot_user in bot_users:
                if bot_user.tg_id in processed_tg_ids:
                    continue
                    
                tg_id = bot_user.tg_id
                computed_hash = hashlib.md5(str(tg_id).encode()).hexdigest()
                
                if computed_hash == remnawave_username:
                    if bot_user.vpn_id != remnawave_username:
                        await update_vpn_id(tg_id, remnawave_username)
                        updated += 1
                        print(f"✓ Обновлен tg_id={tg_id}: {bot_user.vpn_id} -> {remnawave_username}")
                    else:
                        already_correct += 1
                    processed_tg_ids.add(tg_id)
                    found_match = True
                    break
        
        if not found_match:
            remnawave_not_in_bot.append(remnawave_username)
    
    for bot_user in bot_users:
        if bot_user.tg_id not in processed_tg_ids:
            not_found += 1
            if not_found <= 10:
                print(f"⚠ Не найден в Remnawave: tg_id={bot_user.tg_id}, vpn_id={bot_user.vpn_id}")
    
    if not_found > 10:
        print(f"⚠ ... и еще {not_found - 10} пользователей не найдено")
    
    print()
    print("=" * 50)
    print("РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ:")
    print(f"Обновлено: {updated}")
    print(f"Уже корректно: {already_correct}")
    print(f"Не найдено в Remnawave: {not_found}")
    if remnawave_not_in_bot:
        print(f"Пользователей в Remnawave без записи в БД бота: {len(remnawave_not_in_bot)}")
    print("=" * 50)
    print()
    
    if remnawave_not_in_bot:
        print(f"ВНИМАНИЕ: {len(remnawave_not_in_bot)} пользователей из Remnawave не найдены в БД бота.")
        print("Это означает, что эти пользователи были созданы в Remnawave, но не имеют записи в БД бота.")
        print("Примеры (первые 5):")
        for username in remnawave_not_in_bot[:5]:
            print(f"  - {username}")
        if len(remnawave_not_in_bot) > 5:
            print(f"  ... и еще {len(remnawave_not_in_bot) - 5}")
        print()
    
    if not_found > 0:
        print("ВНИМАНИЕ: Некоторые пользователи из БД бота не найдены в Remnawave.")
        print("Это может означать, что:")
        print("1. Пользователи еще не были мигрированы в Remnawave")
        print("2. Username в Remnawave отличаются от vpn_id в БД бота")
        print("3. Пользователи были удалены из Remnawave")
        print()
    
    if updated == 0 and already_correct > 0:
        print("✓ Отлично! Все найденные пользователи уже имеют корректные vpn_id.")
        print("  Миграция прошла успешно, синхронизация не требуется.")
        print()

async def main():
    try:
        await sync_vpn_ids()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

