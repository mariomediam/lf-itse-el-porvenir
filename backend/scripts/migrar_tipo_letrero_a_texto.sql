-- =============================================================================
-- Script de migración: tipo_letrero de FK (integer) a texto (varchar)
--
-- Descripción:
--   Reemplaza la columna tipo_letrero_id (FK a tipos_letrero) en la tabla
--   licencias_funcionamiento por una columna tipo_letrero de tipo VARCHAR(200)
--   que almacena el texto descriptivo directamente.
--
-- Pasos:
--   1. Agregar columna temporal tipo_letrero (varchar)
--   2. Poblar con el nombre del tipo de letrero existente
--   3. Eliminar la FK constraint y la columna tipo_letrero_id
--   4. (Opcional) Eliminar la tabla tipos_letrero si ya no se necesita
--
-- IMPORTANTE: Ejecutar dentro de una transacción.
--             Verificar los datos antes de hacer COMMIT.
-- =============================================================================

BEGIN;

-- Paso 1: Agregar nueva columna tipo_letrero (varchar 200)
ALTER TABLE licencias_funcionamiento
    ADD COLUMN tipo_letrero VARCHAR(200);

-- Paso 2: Poblar la nueva columna con el nombre desde la tabla tipos_letrero
UPDATE licencias_funcionamiento lf
SET tipo_letrero = tl.nombre
FROM tipos_letrero tl
WHERE lf.tipo_letrero_id = tl.id;

-- Paso 2b: Para registros que no tengan coincidencia (por integridad),
--           asignar cadena vacía
UPDATE licencias_funcionamiento
SET tipo_letrero = ''
WHERE tipo_letrero IS NULL;

-- Paso 3: Establecer la columna como NOT NULL
ALTER TABLE licencias_funcionamiento
    ALTER COLUMN tipo_letrero SET NOT NULL;

-- Paso 4: Eliminar la constraint FK de tipo_letrero_id
-- (El nombre de la constraint puede variar; este query la busca dinámicamente)
DO $$
DECLARE
    v_constraint_name TEXT;
BEGIN
    SELECT tc.constraint_name
    INTO v_constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'licencias_funcionamiento'
        AND kcu.column_name = 'tipo_letrero_id';

    IF v_constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE licencias_funcionamiento DROP CONSTRAINT ' || v_constraint_name;
        RAISE NOTICE 'FK constraint eliminada: %', v_constraint_name;
    ELSE
        RAISE NOTICE 'No se encontró FK constraint para tipo_letrero_id';
    END IF;
END $$;

-- Paso 5: Eliminar la columna tipo_letrero_id
ALTER TABLE licencias_funcionamiento
    DROP COLUMN tipo_letrero_id;

-- =============================================================================
-- Verificación: consultar los datos migrados
-- =============================================================================
SELECT id, numero_licencia, tipo_letrero
FROM licencias_funcionamiento
ORDER BY id
LIMIT 20;

-- =============================================================================
-- (Opcional) Paso 6: Eliminar la tabla tipos_letrero si ya no se usa
-- Descomentar las líneas siguientes si se desea eliminar la tabla.
-- =============================================================================
-- DROP TABLE IF EXISTS tipos_letrero;

-- Si todo está correcto:
COMMIT;

-- Si algo salió mal:
-- ROLLBACK;
