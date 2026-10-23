--[[
	Animations d'un gardien (Steal an Egg) : Bélier Colosse, Rat Ravageur, Loup des Ronces… (mêmes noms de clips pour tous)

	Où le mettre : un Script (serveur) directement dans le modèle du gardien importé
	(ex. Workspace > Gardien_Prairie_Belier_rig ou Gardien_Champ_Rat_rig).

	Avant : publier chaque animation depuis l'Animation Editor et coller les ID ci-dessous.

	Ce que fait le script :
	  - joue « Marche » quand le modèle se déplace, puis « Course » quand il va vite
	    (vitesse de l'animation adaptée à la vitesse réelle) ; à l'arrêt il garde sa pose ;
	  - joue le coup de croc quand un autre script fait :
	        gardien:SetAttribute("Action", "CoupDeCroc")
	  - le fait dormir / le réveille :
	        gardien:SetAttribute("Dort", true)   -- puis false pour le réveiller
]]

local RunService = game:GetService("RunService")

local modele = script.Parent

local IDS = {
	Marche = "rbxassetid://0",
	Course = "rbxassetid://0",
	Sommeil = "rbxassetid://0",
	CoupDeCroc = "rbxassetid://0",
}

-- vitesses (studs/s) auxquelles les animations tournent à vitesse normale
-- Bélier : 4,5 et 11,5 — Rat : 3,9 et 8,5 — Loup : 5,1 et 10,9
local VITESSE_MARCHE = 4.5
local VITESSE_COURSE = 11.5
-- au-dessus de cette vitesse, il court au lieu de marcher (Bélier : 8 — Rat : 6 — Loup : 8)
local SEUIL_COURSE = 8

local controleur = modele:FindFirstChildOfClass("Humanoid") or modele:FindFirstChildOfClass("AnimationController")
if not controleur then
	controleur = Instance.new("AnimationController")
	controleur.Parent = modele
end
local animateur = controleur:FindFirstChildOfClass("Animator")
if not animateur then
	animateur = Instance.new("Animator")
	animateur.Parent = controleur
end

local pistes = {}
for nom, id in pairs(IDS) do
	local animation = Instance.new("Animation")
	animation.Name = nom
	animation.AnimationId = id
	pistes[nom] = animateur:LoadAnimation(animation)
end

pistes.Marche.Looped = true
pistes.Marche.Priority = Enum.AnimationPriority.Movement
pistes.Course.Looped = true
pistes.Course.Priority = Enum.AnimationPriority.Movement
pistes.Sommeil.Looped = true
pistes.Sommeil.Priority = Enum.AnimationPriority.Action
pistes.CoupDeCroc.Looped = false
pistes.CoupDeCroc.Priority = Enum.AnimationPriority.Action2

-- joue une seule des deux allures (ou aucune) et arrête l'autre
local function allure(active, vitesseAnim)
	for _, nom in ipairs({ "Marche", "Course" }) do
		local piste = pistes[nom]
		if nom == active then
			if not piste.IsPlaying then
				piste:Play(0.25)
			end
			piste:AdjustSpeed(vitesseAnim)
		elseif piste.IsPlaying then
			piste:Stop(0.3)
		end
	end
end

-- marche / course selon la vitesse réelle du gardien
local dernierePosition = modele:GetPivot().Position
RunService.Heartbeat:Connect(function(dt)
	local position = modele:GetPivot().Position
	local deplacement = (position - dernierePosition) * Vector3.new(1, 0, 1)
	dernierePosition = position
	local vitesse = deplacement.Magnitude / math.max(dt, 1e-3)
	if modele:GetAttribute("Dort") or vitesse <= 0.5 then
		allure(nil, 1)
	elseif vitesse < SEUIL_COURSE then
		allure("Marche", math.clamp(vitesse / VITESSE_MARCHE, 0.5, 2))
	else
		allure("Course", math.clamp(vitesse / VITESSE_COURSE, 0.7, 2))
	end
end)

-- sommeil
modele:GetAttributeChangedSignal("Dort"):Connect(function()
	if modele:GetAttribute("Dort") then
		pistes.Sommeil:Play(1.0) -- se couche en douceur
	else
		pistes.Sommeil:Stop(0.8) -- se relève
	end
end)

-- coup de croc déclenché par un attribut
modele:GetAttributeChangedSignal("Action"):Connect(function()
	local action = modele:GetAttribute("Action")
	if action == nil then
		return
	end
	modele:SetAttribute("Action", nil)
	local piste = pistes[action]
	if piste then
		piste:Play(0.1)
	else
		warn("Action inconnue pour le gardien : " .. tostring(action))
	end
end)
