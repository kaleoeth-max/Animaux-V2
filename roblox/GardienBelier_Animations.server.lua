--[[
	Animations du Bélier Colosse (gardien de la Prairie, Steal an Egg)

	Où le mettre : un Script (serveur) directement dans le modèle du Bélier importé
	(Workspace > Gardien_Prairie_Belier_rig).

	Avant : publier chaque animation depuis l'Animation Editor et coller les ID ci-dessous.

	Ce que fait le script :
	  - joue « Repos » en boucle ;
	  - passe à « Marche » dès que le modèle se déplace (vitesse de l'animation adaptée à la vitesse) ;
	  - joue une attaque quand un autre script fait :
	        gardien:SetAttribute("Action", "Morsure")      -- ou "Rugissement", "CoupDeQueue"
]]

local RunService = game:GetService("RunService")

local modele = script.Parent

local IDS = {
	Repos = "rbxassetid://0",
	Marche = "rbxassetid://0",
	Morsure = "rbxassetid://0",
	Rugissement = "rbxassetid://0",
	CoupDeQueue = "rbxassetid://0",
}

-- vitesse (studs/s) à laquelle l'animation de marche tourne à vitesse normale
local VITESSE_MARCHE = 4.5

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

pistes.Repos.Looped = true
pistes.Repos.Priority = Enum.AnimationPriority.Idle
pistes.Marche.Looped = true
pistes.Marche.Priority = Enum.AnimationPriority.Movement
for _, nom in ipairs({ "Morsure", "Rugissement", "CoupDeQueue" }) do
	pistes[nom].Looped = false
	pistes[nom].Priority = Enum.AnimationPriority.Action
end

pistes.Repos:Play()

-- marche quand le gardien se déplace
local dernierePosition = modele:GetPivot().Position
RunService.Heartbeat:Connect(function(dt)
	local position = modele:GetPivot().Position
	local deplacement = (position - dernierePosition) * Vector3.new(1, 0, 1)
	dernierePosition = position
	local vitesse = deplacement.Magnitude / math.max(dt, 1e-3)
	if vitesse > 0.5 then
		if not pistes.Marche.IsPlaying then
			pistes.Marche:Play(0.25)
		end
		pistes.Marche:AdjustSpeed(math.clamp(vitesse / VITESSE_MARCHE, 0.5, 2.5))
	elseif pistes.Marche.IsPlaying then
		pistes.Marche:Stop(0.3)
	end
end)

-- attaques déclenchées par un attribut
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
