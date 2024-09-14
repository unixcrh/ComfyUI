from typing import TYPE_CHECKING, Dict, List, Tuple
import torch

if TYPE_CHECKING:
    from comfy.model_patcher import ModelPatcher
    from comfy.sd import CLIP

import comfy.hooks
import comfy.sd
import folder_paths

###########################################
# Mask, Combine, and Hook Conditioning
#------------------------------------------
class PairConditioningSetProperties:
    NodeId = 'PairConditioningSetProperties'
    NodeName = 'Pair Cond Set Props'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive_NEW": ("CONDITIONING", ),
                "negative_NEW": ("CONDITIONING", ),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "set_cond_area": (["default", "mask bounds"],),
            },
            "optional": {
                "opt_mask": ("MASK", ),
                "opt_hooks": ("HOOKS",),
                "opt_timesteps": ("TIMESTEPS_RANGE",),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    CATEGORY = "advanced/hooks/cond pair"
    FUNCTION = "set_properties"

    def set_properties(self, positive_NEW, negative_NEW,
                       strength: float, set_cond_area: str,
                       opt_mask: torch.Tensor=None, opt_hooks: comfy.hooks.Hook=None, opt_timesteps: Tuple=None):
        final_positive, final_negative = comfy.hooks.set_mask_conds(conds=[positive_NEW, negative_NEW],
                                                                    strength=strength, set_cond_area=set_cond_area,
                                                                    opt_mask=opt_mask, opt_hooks=opt_hooks, opt_timestep_range=opt_timesteps)
        return (final_positive, final_negative)

class ConditioningSetProperties:
    NodeId = 'ConditioningSetProperties'
    NodeName = 'Cond Set Props'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cond_NEW": ("CONDITIONING", ),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "set_cond_area": (["default", "mask bounds"],),
            },
            "optional": {
                "opt_mask": ("MASK", ),
                "opt_hooks": ("HOOKS",),
                "opt_timesteps": ("TIMESTEPS_RANGE",),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("positive", "negative")
    CATEGORY = "advanced/hooks/cond single"
    FUNCTION = "set_properties"

    def set_properties(self, cond_NEW,
                       strength: float, set_cond_area: str,
                       opt_mask: torch.Tensor=None, opt_hooks: comfy.hooks.Hook=None, opt_timesteps: Tuple=None):
        (final_cond,) = comfy.hooks.set_mask_conds(conds=[cond_NEW],
                                                                    strength=strength, set_cond_area=set_cond_area,
                                                                    opt_mask=opt_mask, opt_hooks=opt_hooks, opt_timestep_range=opt_timesteps)
        return (final_cond,)

class PairConditioningCombine:
    NodeId = 'PairConditioningCombine'
    NodeName = 'Pair Cond Combine'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive_A": ("CONDITIONING",),
                "negative_A": ("CONDITIONING",),
                "positive_B": ("CONDITIONING",),
                "negative_B": ("CONDITIONING",),
            },
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    CATEGORY = "advanced/hooks/cond pair"
    FUNCTION = "combine"

    def combine(self, positive_A, negative_A, positive_B, negative_B):
        final_positive, final_negative = comfy.hooks.set_mask_and_combine_conds(conds=[positive_A, negative_A], new_conds=[positive_B, negative_B],)
        return (final_positive, final_negative,)

class PairConditioningSetDefaultAndCombine:
    NodeId = 'PairConditioningSetDefaultCombine'
    NodeName = 'Pair Cond Set Default Combine'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "positive_DEFAULT": ("CONDITIONING",),
                "negative_DEFAULT": ("CONDITIONING",),
            },
            "optional": {
                "opt_hooks": ("HOOKS",),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    CATEGORY = "advanced/hooks/cond pair"
    FUNCTION = "set_default_and_combine"

    def set_default_and_combine(self, positive, negative, positive_DEFAULT, negative_DEFAULT,
                                opt_hooks: comfy.hooks.HookGroup=None):
        final_positive, final_negative = comfy.hooks.set_default_and_combine_conds(conds=[positive, negative], new_conds=[positive_DEFAULT, negative_DEFAULT],
                                                                                   opt_hooks=opt_hooks)
        return (final_positive, final_negative)
    
class ConditioningSetDefaultAndCombine:
    NodeId = 'ConditioningSetDefaultCombine'
    NodeName = 'Cond Set Default Combine'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cond": ("CONDITIONING",),
                "cond_DEFAULT": ("CONDITIONING",),
            },
            "optional": {
                "opt_hooks": ("HOOKS",),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    CATEGORY = "advanced/hooks/cond single"
    FUNCTION = "set_default_and_combine"

    def append_and_combine(self, cond, cond_DEFAULT,
                           opt_hooks: comfy.hooks.HookGroup=None):
        (final_conditioning,) = comfy.hooks.set_default_and_combine_conds(conds=[cond], new_conds=[cond_DEFAULT],
                                                                        opt_hooks=opt_hooks)
        return (final_conditioning,)
#------------------------------------------
###########################################


###########################################
# Register Hooks
#------------------------------------------
class RegisterHookLora:
    NodeId = 'RegisterHookLora'
    NodeName = 'Register Hook LoRA'
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (folder_paths.get_filename_list("loras"), ),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "HOOKS")
    CATEGORY = "advanced/hooks/register"
    FUNCTION = "register_lora"

    def register_lora(self, model: 'ModelPatcher', clip: 'CLIP', lora_name: str,
                      strength_model: float, strength_clip: float):
        if strength_model == 0 and strength_clip == 0:
            return (model, clip, None)
        
        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                temp = self.loaded_lora
                self.loaded_lora = None
                del temp
        
        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)
        
        hook = comfy.hooks.Hook()
        hook_group = comfy.hooks.HookGroup()
        hook_group.add(hook)
        model_lora, clip_lora = comfy.hooks.load_hook_lora_for_models(model=model, clip=clip, lora=lora, hook=hook,
                                                                      strength_model=strength_model, strength_clip=strength_clip)
        return (model_lora, clip_lora, hook_group)

class RegisterHookLoraModelOnly(RegisterHookLora):
    NodeId = 'RegisterHookLoraModelOnly'
    NodeName = 'Register Hook LoRA (MO)'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (folder_paths.get_filename_list("loras"), ),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "HOOKS")
    CATEGORY = "advanced/hooks/register"
    FUNCTION = "register_lora_model_only"

    def register_lora_model_only(self, model: 'ModelPatcher', lora_name: str, strength_model: float):
        model_lora, _, hooks = self.register_lora(model=model, clip=None, lora_name=lora_name,
                                                 strength_model=strength_model, strength_clip=0)
        return (model_lora, hooks)

class RegisterHookModelAsLora:
    NodeId = 'RegisterHookModelAsLora'
    NodeName = 'Register Hook Model as LoRA'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"), ),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "HOOKS")
    CATEGORY = "advanced/hooks/register"
    FUNCTION = "register_model_as_lora"

    def register_model_as_lora(self, model: 'ModelPatcher', clip: 'CLIP', ckpt_name: str,
                                 strength_model: float, strength_clip: float):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
        model_loaded = out[0]
        clip_loaded = out[1]

        hook = comfy.hooks.Hook()
        hook_group = comfy.hooks.HookGroup()
        hook_group.add(hook)
        model_lora, clip_lora = comfy.hooks.load_hook_model_as_lora_for_models(model=model, clip=clip,
                                                                               model_loaded=model_loaded, clip_loaded=clip_loaded,
                                                                               hook=hook,
                                                                               strength_model=strength_model, strength_clip=strength_clip)
        return (model_lora, clip_lora, hook_group)

class RegisterHookModelAsLoraModelOnly:
    NodeId = 'RegisterHookModelAsLoraModelOnly'
    NodeName = 'Register Hook Model as LoRA (MO)'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"), ),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "HOOKS")
    CATEGORY = "advanced/hooks/register"
    FUNCTION = "register_model_as_lora_model_only"

    def register_model_as_lora_model_only(self, model: 'ModelPatcher', ckpt_name: str, strength_model: float):
        model_lora, _, hooks = RegisterHookModelAsLora.register_model_as_lora(self, model=model, clip=None, ckpt_name=ckpt_name,
                                                                              strength_model=strength_model, strength_clip=0)
        return (model_lora, hooks)
#------------------------------------------
###########################################


###########################################
# Schedule Hooks
#------------------------------------------
#------------------------------------------
###########################################


class SetModelHooksOnCond:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "hooks": ("HOOKS",),
            },
        }
    
    RETURN_TYPES = ("CONDITIONING",)
    CATEGORY = "advanced/hooks/manual"
    FUNCTION = "attach_hook"

    def attach_hook(self, conditioning, hooks: comfy.hooks.HookGroup):
        return (comfy.hooks.set_hooks_for_conditioning(conditioning, hooks),)


###########################################
# Combine Hooks
#------------------------------------------
class CombineHooks:
    NodeId = 'CombineHooks2'
    NodeName = 'Combine Hooks [2]'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "optional": {
                "hooks_A": ("HOOKS",),
                "hooks_B": ("HOOKS",),
            }
        }
    
    RETURN_TYPES = ("HOOKS",)
    CATEGORY = "advanced/hooks/combine"
    FUNCTION = "combine_hooks"

    def combine_hooks(self,
                      hooks_A: comfy.hooks.HookGroup=None,
                      hooks_B: comfy.hooks.HookGroup=None):
        candidates = [hooks_A, hooks_B]
        return (comfy.hooks.HookGroup.combine_all_hooks(candidates),)

class CombineHooksFour:
    NodeId = 'CombineHooks4'
    NodeName = 'Combine Hooks [4]'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "optional": {
                "hooks_A": ("HOOKS",),
                "hooks_B": ("HOOKS",),
                "hooks_C": ("HOOKS",),
                "hooks_D": ("HOOKS",),
            }
        }
    
    RETURN_TYPES = ("HOOKS",)
    CATEGORY = "advanced/hooks/combine"
    FUNCTION = "combine_hooks"

    def combine_hooks(self,
                      hooks_A: comfy.hooks.HookGroup=None,
                      hooks_B: comfy.hooks.HookGroup=None,
                      hooks_C: comfy.hooks.HookGroup=None,
                      hooks_D: comfy.hooks.HookGroup=None):
        candidates = [hooks_A, hooks_B, hooks_C, hooks_D]
        return (comfy.hooks.HookGroup.combine_all_hooks(candidates),)

class CombineHooksEight:
    NodeId = 'CombineHooks8'
    NodeName = 'Combine Hooks [8]'
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "optional": {
                "hooks_A": ("HOOKS",),
                "hooks_B": ("HOOKS",),
                "hooks_C": ("HOOKS",),
                "hooks_D": ("HOOKS",),
                "hooks_E": ("HOOKS",),
                "hooks_F": ("HOOKS",),
                "hooks_G": ("HOOKS",),
                "hooks_H": ("HOOKS",),
            }
        }
    
    RETURN_TYPES = ("HOOKS",)
    CATEGORY = "advanced/hooks/combine"
    FUNCTION = "combine_hooks"

    def combine_hooks(self,
                      hooks_A: comfy.hooks.HookGroup=None,
                      hooks_B: comfy.hooks.HookGroup=None,
                      hooks_C: comfy.hooks.HookGroup=None,
                      hooks_D: comfy.hooks.HookGroup=None,
                      hooks_E: comfy.hooks.HookGroup=None,
                      hooks_F: comfy.hooks.HookGroup=None,
                      hooks_G: comfy.hooks.HookGroup=None,
                      hooks_H: comfy.hooks.HookGroup=None):
        candidates = [hooks_A, hooks_B, hooks_C, hooks_D, hooks_E, hooks_F, hooks_G, hooks_H]
        return (comfy.hooks.HookGroup.combine_all_hooks(candidates),)
#------------------------------------------
###########################################

node_list = [
    # Register
    RegisterHookLora,
    RegisterHookLoraModelOnly,
    RegisterHookModelAsLora,
    RegisterHookModelAsLoraModelOnly,
    # Combine
    CombineHooks,
    CombineHooksFour,
    CombineHooksEight,
    # Attach
    ConditioningSetProperties,
    PairConditioningSetProperties,
    ConditioningSetDefaultAndCombine,
    PairConditioningSetDefaultAndCombine,
    PairConditioningCombine
]
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for node in node_list:
    NODE_CLASS_MAPPINGS[node.NodeId] = node
    NODE_DISPLAY_NAME_MAPPINGS[node.NodeId] = node.NodeName