-- 자료 공유센터: 즐겨찾기 + 휴지통 + 자료 수정
ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS deleted_at timestamptz NULL;
ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS updated_at timestamptz NULL;
ALTER TABLE public.materials ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "materials_select_authenticated" ON public.materials;
CREATE POLICY "materials_select_authenticated" ON public.materials FOR SELECT TO authenticated USING (deleted_at IS NULL OR owner_id=auth.uid() OR EXISTS (SELECT 1 FROM public.admin_users WHERE user_id=auth.uid()));
DROP POLICY IF EXISTS "materials_update_owner" ON public.materials;
DROP POLICY IF EXISTS "materials_update_owner_or_admin" ON public.materials;
CREATE POLICY "materials_update_owner_or_admin" ON public.materials FOR UPDATE TO authenticated USING (owner_id=auth.uid() OR EXISTS (SELECT 1 FROM public.admin_users WHERE user_id=auth.uid())) WITH CHECK (owner_id=auth.uid() OR EXISTS (SELECT 1 FROM public.admin_users WHERE user_id=auth.uid()));
CREATE TABLE IF NOT EXISTS public.material_favorites (user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, material_id uuid NOT NULL REFERENCES public.materials(id) ON DELETE CASCADE, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(user_id,material_id));
ALTER TABLE public.material_favorites ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "favorites_select_own" ON public.material_favorites;
CREATE POLICY "favorites_select_own" ON public.material_favorites FOR SELECT TO authenticated USING (user_id=auth.uid());
DROP POLICY IF EXISTS "favorites_insert_own" ON public.material_favorites;
CREATE POLICY "favorites_insert_own" ON public.material_favorites FOR INSERT TO authenticated WITH CHECK (user_id=auth.uid());
DROP POLICY IF EXISTS "favorites_delete_own" ON public.material_favorites;
CREATE POLICY "favorites_delete_own" ON public.material_favorites FOR DELETE TO authenticated USING (user_id=auth.uid());
GRANT SELECT,INSERT,DELETE ON public.material_favorites TO authenticated;