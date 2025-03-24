from django.db import migrations

class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS search_functions_init(id integer primary key);
            
            CREATE FUNCTION IF NOT EXISTS remove_accents(text TEXT) 
            RETURNS TEXT AS 
            WITH chars(accented, unaccented) AS (
                SELECT 'áàâãäçéèêëíìîïñóòôõöúùûüýÿÁÀÂÃÄÇÉÈÊËÍÌÎÏÑÓÒÔÕÖÚÙÛÜÝ',
                       'aaaaaceeeeiiiinooooouuuuyyAAAAACEEEEIIIINOOOOOUUUUY'
            )
            SELECT LOWER(
                (
                    WITH RECURSIVE t(remainder, normalized) AS (
                        SELECT SUBSTR($1, 2), 
                            CASE 
                                WHEN INSTR(
                                    (SELECT accented FROM chars), 
                                    SUBSTR($1, 1, 1)
                                ) > 0 
                                THEN SUBSTR(
                                    (SELECT unaccented FROM chars), 
                                    INSTR(
                                        (SELECT accented FROM chars), 
                                        SUBSTR($1, 1, 1)
                                    ), 
                                    1
                                )
                                ELSE SUBSTR($1, 1, 1)
                            END
                        UNION ALL
                        SELECT SUBSTR(remainder, 2), 
                            normalized || 
                            CASE 
                                WHEN INSTR(
                                    (SELECT accented FROM chars), 
                                    SUBSTR(remainder, 1, 1)
                                ) > 0 
                                THEN SUBSTR(
                                    (SELECT unaccented FROM chars), 
                                    INSTR(
                                        (SELECT accented FROM chars), 
                                        SUBSTR(remainder, 1, 1)
                                    ), 
                                    1
                                )
                                ELSE SUBSTR(remainder, 1, 1)
                            END
                        FROM t 
                        WHERE remainder != ''
                    )
                    SELECT normalized FROM t ORDER BY LENGTH(normalized) DESC LIMIT 1
                )
            );
            """,
            reverse_sql="DROP FUNCTION IF EXISTS remove_accents;"
        )
    ]