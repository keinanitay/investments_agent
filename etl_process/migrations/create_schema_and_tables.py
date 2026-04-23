"""
Migration: יצירת סכמה ten_years_back_data והטבלאות trade_data ו-ex_code
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from db_schema import Base, TradeData, ExCode

# טעינת משתני סביבה
load_dotenv()

# בניית connection string
conn_string = f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DATABASE')}"

def run_migration():
    """
    מריץ את ה-migration:
    1. יוצר את הסכמה ten_years_back_data
    2. יוצר את הטבלאות trade_data ו-ex_code
    3. יוצר את כל האינדקסים אוטומטית
    """
    
    print("🚀 מתחיל migration...")
    
    # יצירת engine
    engine = create_engine(conn_string, echo=True)
    
    try:
        # שלב 1: יצירת הסכמה
        print("\n📁 יוצר סכמה: ten_years_back_data")
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS ten_years_back_data;"))
            conn.commit()
        print("✅ הסכמה נוצרה בהצלחה")
        
        # שלב 2: יצירת הטבלאות עם כל האינדקסים
        print("\n📊 יוצר טבלאות ואינדקסים...")
        Base.metadata.create_all(engine)
        print("✅ הטבלאות והאינדקסים נוצרו בהצלחה")
        
        # שלב 3: וידוא שהטבלאות נוצרו
        print("\n🔍 מוודא שהטבלאות נוצרו...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'ten_years_back_data'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
            print(f"\n✅ טבלאות שנוצרו בסכמה ten_years_back_data:")
            for table in tables:
                print(f"   - {table}")
            
            # בדיקת אינדקסים
            print(f"\n🔍 בדיקת אינדקסים...")
            result = conn.execute(text("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'ten_years_back_data'
                ORDER BY tablename, indexname;
            """))
            
            print(f"\n✅ אינדקסים שנוצרו:")
            for row in result:
                print(f"   📌 {row[0]}.{row[1]}")
        
        print("\n" + "="*60)
        print("🎉 Migration הושלם בהצלחה!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ שגיאה במהלך ה-migration: {e}")
        raise
    
    finally:
        engine.dispose()


def rollback_migration():
    """
    מבטל את ה-migration - מוחק את הסכמה כולל כל הטבלאות
    ⚠️ שימוש בזהירות! פעולה זו מוחקת את כל הנתונים!
    """
    
    print("⚠️  מתחיל rollback - מחיקת הסכמה וכל התוכן שלה...")
    
    engine = create_engine(conn_string, echo=True)
    
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS ten_years_back_data CASCADE;"))
            conn.commit()
        print("✅ הסכמה נמחקה בהצלחה")
        
    except Exception as e:
        print(f"❌ שגיאה במהלך rollback: {e}")
        raise
    
    finally:
        engine.dispose()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        # הרצת rollback
        confirm = input("⚠️  האם אתה בטוח שברצונך למחוק את הסכמה וכל הנתונים? (yes/no): ")
        if confirm.lower() == "yes":
            rollback_migration()
        else:
            print("❌ פעולת rollback בוטלה")
    else:
        # הרצת migration רגיל
        run_migration()

