from .dbcommands import DataBase


class Groups(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."Groups"
(
                   user_group varchar(255) PRIMARY KEY,
                   add_or_delete_group boolean DEFAULT FALSE,
                   update_user_group boolean DEFAULT FALSE,
                   update_permissions_subgroup boolean DEFAULT FALSE,
                   update_faq boolean DEFAULT FALSE
);
                '''
        await self.connector.execute(query)

    async def add(self, new_group,
                  add_or_delete_group=False, update_user_group=False,
                  update_permissions_subgroup=False, update_faq=False):
        query = '''INSERT INTO public."Groups"
        (user_group, add_or_delete_group, update_user_group, update_permissions_subgroup, update_faq)
                    VALUES ($1, $2, $3, $4, $5) ON CONFLICT (user_group) 
                    DO UPDATE SET
                    add_or_delete_group=$2, update_user_group=$3, 
                    update_permissions_subgroup=$4, update_faq=$5;
                '''
        await self.connector.execute(query, new_group,
                                     add_or_delete_group, update_user_group, update_permissions_subgroup, update_faq)

    async def get(self):
        query = '''
        
        SELECT G.user_group, G.add_or_delete_group, G.update_user_group, G.update_permissions_subgroup, G.update_faq,
        COALESCE(array_agg(DISTINCT SG.subordinate_group), ARRAY[NULL]::VARCHAR[]) as subordinate_groups
        FROM "Groups" G
        LEFT JOIN "SGroups" SG ON SG.user_group = G.user_group
        GROUP BY G.user_group, G.add_or_delete_group, G.update_user_group, G.update_permissions_subgroup, G.update_faq
        ORDER BY G.user_group;
        
                '''
        return await self.connector.fetch(query)

    async def del_(self, user_group: str):
        query = '''DELETE FROM public."Groups" WHERE user_group=$1;
                '''
        await self.connector.execute(query, user_group)




class SGroups(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."SGroups"(
                   id serial PRIMARY KEY ,
                   user_group varchar(255) REFERENCES "Groups" ON DELETE CASCADE,
                   subordinate_group varchar(255) REFERENCES "Groups" ON DELETE CASCADE,
                   CHECK ( NOT user_group = subordinate_group),
                   UNIQUE (user_group, subordinate_group)
                   );
                    CREATE OR REPLACE FUNCTION check_cyclic_reference()
                    RETURNS TRIGGER AS $$
                    BEGIN
                      IF EXISTS (
                        SELECT *
                        FROM "SGroups"
                        WHERE "SGroups".user_group = NEW.subordinate_group
                        AND "SGroups".subordinate_group = NEW.user_group
                      ) THEN
                        RAISE EXCEPTION 'Рекурсивное/циклическое объявление запрещено!';
                      END IF;
                    
                      RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                    DO $$
                    BEGIN
                      IF NOT EXISTS (
                        SELECT 1
                        FROM pg_trigger
                        WHERE tgname = 'cyclic_reference'
                      ) THEN
                        CREATE TRIGGER cyclic_reference
                        BEFORE INSERT OR UPDATE
                        ON "SGroups"
                        FOR EACH ROW
                        EXECUTE PROCEDURE check_cyclic_reference();
                      END IF;
                    END;
                    $$;
                '''
        await self.connector.execute(query)

    async def add_one(self, group:str, subordinate_group:str):
        query = '''
                INSERT INTO "SGroups" (user_group, subordinate_group)
                VALUES ($1, $2) ON CONFLICT DO NOTHING
                '''
        await self.connector.execute(query, group, subordinate_group)

    async def add(self, group:str, sgroup: str):
        query = '''WITH RECURSIVE
                    add_relation AS (
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        RETURNING *
                    ),
                    subgroups_of_a AS (
                        SELECT subordinate_group
                        FROM "SGroups"
                        WHERE user_group = $2
                        UNION
                        SELECT s.subordinate_group
                        FROM "SGroups" s
                        INNER JOIN subgroups_of_a ON subgroups_of_a.subordinate_group = s.user_group
                    ),
                    add_subgroups_of_a AS (
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        SELECT $1, s.subordinate_group
                        FROM subgroups_of_a s
                        ON CONFLICT DO NOTHING
                    ),
                    parent_groups AS (
                        SELECT s1.user_group AS parent_group
                        FROM "SGroups" s1
                        WHERE s1.subordinate_group = $1
                        UNION
                        SELECT s2.user_group
                        FROM "SGroups" s2
                        INNER JOIN parent_groups ON parent_groups.parent_group = s2.subordinate_group
                    ),
                    add_relation_managers AS (
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        RETURNING *
                    ),
                    subgroups_of_prem AS (
                        SELECT $2 AS subordinate_group
                        UNION
                        SELECT s.subordinate_group
                        FROM "SGroups" s
                        WHERE s.user_group = $2
                        UNION
                        SELECT s2.subordinate_group
                        FROM "SGroups" s2
                        INNER JOIN subgroups_of_prem ON subgroups_of_prem.subordinate_group = s2.user_group
                    )
                    INSERT INTO "SGroups" (user_group, subordinate_group)
                    SELECT p.parent_group, s.subordinate_group
                    FROM parent_groups p, subgroups_of_prem s
                    WHERE p.parent_group != s.subordinate_group
                    ON CONFLICT DO NOTHING;
                '''
        await self.connector.execute(query, group, sgroup)

    async def create_func(self):
        query = ''' CREATE OR REPLACE FUNCTION update_group_hierarchy(
                        parent_group VARCHAR,
                        child_group VARCHAR
                    )
                    RETURNS void AS $$
                    BEGIN
                        -- Добавление связи между parent_group и child_group
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        VALUES (parent_group, child_group)
                        ON CONFLICT DO NOTHING;
                    
                        -- Рекурсивное добавление подгрупп child_group к parent_group
                        WITH RECURSIVE subgroups_of_child AS (
                            SELECT subordinate_group
                            FROM "SGroups"
                            WHERE user_group = child_group
                            UNION
                            SELECT s.subordinate_group
                            FROM "SGroups" s
                            INNER JOIN subgroups_of_child ON subgroups_of_child.subordinate_group = s.user_group
                        )
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        SELECT parent_group, s.subordinate_group
                        FROM subgroups_of_child s
                        ON CONFLICT DO NOTHING;
                    
                        -- Добавление связей между всеми родительскими группами parent_group и child_group
                        WITH RECURSIVE parent_groups AS (
                            SELECT s1.user_group AS parent_group
                            FROM "SGroups" s1
                            WHERE s1.subordinate_group = parent_group
                            UNION
                            SELECT s2.user_group
                            FROM "SGroups" s2
                            INNER JOIN parent_groups ON parent_groups.parent_group = s2.subordinate_group
                        ), subgroups_of_child AS (
                            SELECT child_group AS subordinate_group
                            UNION
                            SELECT s.subordinate_group
                            FROM "SGroups" s
                            WHERE s.user_group = child_group
                            UNION
                            SELECT s2.subordinate_group
                            FROM "SGroups" s2
                            INNER JOIN subgroups_of_child ON subgroups_of_child.subordinate_group = s2.user_group
                        )
                        INSERT INTO "SGroups" (user_group, subordinate_group)
                        SELECT p.parent_group, s.subordinate_group
                        FROM parent_groups p, subgroups_of_child s
                        WHERE p.parent_group != s.subordinate_group
                        ON CONFLICT DO NOTHING;
                    
                    END;
                    $$ LANGUAGE plpgsql;
                '''
        await self.connector.execute(query)

    async def add_(self, parent, daughter):
        query = '''SELECT update_group_hierarchy($1, $2);
                '''
        return await self.connector.fetch(query, parent, daughter)

    async def get(self, group):
        query = f'''
        SELECT array_agg(subordinate_group) as subordinate_groups FROM public."SGroups" WHERE user_group=$1; 
                '''
        return await self.connector.fetchval(query, group)

    async def get_all(self):
        query = '''SELECT user_group, array_agg(subordinate_group) as subordinate_groups FROM public."SGroups" 
                   GROUP BY user_group;
                '''
        return await self.connector.fetch(query)

    async def del_(self, group, subordinate_group):
        query = '''
                    WITH RECURSIVE
            subordinates_of_subordinate AS (
                SELECT subordinate_group
                FROM "SGroups"
                WHERE user_group = $2 -- $2 - удаляемый наследник
                UNION ALL
                SELECT s.subordinate_group
                FROM "SGroups" s
                INNER JOIN subordinates_of_subordinate ON subordinates_of_subordinate.subordinate_group = s.user_group
            ),
            all_subordinates_to_remove AS (
                SELECT subordinate_group
                FROM subordinates_of_subordinate
                UNION
                SELECT $2 -- Добавляем самого наследника к удаляемым
            )
            DELETE FROM "SGroups"
            WHERE user_group = $1 -- $1 - группа, из которой удаляются связи
            AND subordinate_group IN (SELECT subordinate_group FROM all_subordinates_to_remove);
        '''
        await self.connector.execute(query, group, subordinate_group)

    async def del_one(self, group: str, subordinate_group: str):
        query = '''
        DELETE FROM "SGroups" WHERE user_group=$1 AND subordinate_group=$2;
                '''
        await self.connector.execute(query, group, subordinate_group)
