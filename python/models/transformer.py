import torch
import torch.nn as nn
import gymnasium as gym
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class TransformerExtractor(BaseFeaturesExtractor):
    """
    A Transformer-based Feature Extractor for Dict Observation Spaces.
    
    It treats the observation as a sequence of tokens:
    [Instruments, Contact_1, ..., Contact_N, RWR_1, ..., RWR_M, Mission_Token]
    
    The 'Instruments' token attends to all other tokens to gather situational awareness.
    The final feature vector is the output embedding of the 'Instruments' token.
    """
    
    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 128,
        n_heads: int = 4,
        n_layers: int = 2,
        use_amp: bool = False,
        use_checkpointing: bool = True,
    ):
        # We don't know the exact flattened size in advance easily without calc, 
        # but supers constructor needs it.
        super().__init__(observation_space, features_dim)
        
        self.d_model = features_dim
        self.use_amp = bool(use_amp)
        self._use_checkpointing = bool(use_checkpointing)
        
        # 1. Input Projections
        # Read actual dimensions from observation_space
        instruments_dim = observation_space["instruments"].shape[0]
        contacts_shape = observation_space["contacts"].shape  # (N, 5)
        rwr_shape = observation_space["rwr"].shape  # (M, 4)
        mission_dim = observation_space["mission"].shape[0]
        self.has_proprio = "proprio" in observation_space.spaces
        
        self.embed_instruments = nn.Linear(instruments_dim, self.d_model)
        self.embed_contact = nn.Linear(contacts_shape[1], self.d_model)
        self.embed_rwr = nn.Linear(rwr_shape[1], self.d_model)
        self.embed_mission = nn.Linear(mission_dim, self.d_model)
        if self.has_proprio:
            proprio_dim = observation_space["proprio"].shape[0]
            self.embed_proprio = nn.Linear(proprio_dim, self.d_model)
        else:
            self.embed_proprio = None
        
        # Learnable "Type Embeddings" to distinguish token sources
        # 0=Instruments, 1=Contact, 2=RWR, 3=Mission, 4=Proprio(optional)
        self.type_embed = nn.Embedding(5 if self.has_proprio else 4, self.d_model)
        
        # Register type indices as buffers (not parameters, but move with model)
        self.register_buffer('idx_inst', torch.tensor(0))
        self.register_buffer('idx_contact', torch.tensor(1))
        self.register_buffer('idx_rwr', torch.tensor(2))
        self.register_buffer('idx_mission', torch.tensor(3))
        if self.has_proprio:
            self.register_buffer('idx_proprio', torch.tensor(4))
        
        # 2. Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=n_heads,
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers, enable_nested_tensor=False)
        
        # 3. Output Head
        # We just use the first token (Instruments) as the summary representation
        # So no extra pooling layer needed effectively, just identity or layernorm
        self.ln_final = nn.LayerNorm(self.d_model)
        
        # Verification
        # Total tokens = 1 (Self) + 10 (Contacts) + 4 (RWR) + 1 (Mission) = 16
        
    def forward(self, observations: dict) -> torch.Tensor:
        with torch.autocast("cuda", enabled=(torch.cuda.is_available() and self.use_amp)):
            # 1. Get Components
            # shapes: (Batch, 24), (Batch, 10, 5), (Batch, 4, 4), (Batch, 4)
            s_inst = observations["instruments"]
            s_contacts = observations["contacts"]
            s_rwr = observations["rwr"]
            s_mission = observations["mission"]
            
            batch_size = s_inst.shape[0]
            
            # 2. Embed (using pre-registered buffer indices)
            # (B, 24) -> (B, 1, d_model)
            emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(self.idx_inst)
            
            # (B, 10, 5) -> (B, 10, d_model)
            emb_contacts = self.embed_contact(s_contacts) + self.type_embed(self.idx_contact)
            
            # (B, 4, 4) -> (B, 4, d_model)
            emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(self.idx_rwr)
            
            # (B, 4) -> (B, 1, d_model)
            emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(self.idx_mission)
            emb_parts = [emb_inst, emb_mission]
            if self.has_proprio:
                s_proprio = observations["proprio"]
                emb_proprio = self.embed_proprio(s_proprio).unsqueeze(1) + self.type_embed(self.idx_proprio)
                emb_parts.append(emb_proprio)
            
            # 3. Concat Sequence
            # Order: [Instruments, Mission, Proprio?, Contacts..., RWR...]
            sequence = torch.cat([*emb_parts, emb_contacts, emb_rwr], dim=1)
            
            # 4. Transform with optional gradient checkpointing
            # Masking: We could mask empty contacts/rwr if we had a valid mask. 
            # UniversalEnv pads with 0. 0-padding is a valid input for NN, though attention might check it.
            # For now, we assume all slots are potentially relevant (even 0s imply "empty/no info").
            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint
                # Apply checkpointing to each layer individually
                x = sequence
                for layer in self.transformer.layers:
                    x = checkpoint(layer, x, use_reentrant=False)
                transformed = x
            else:
                transformed = self.transformer(sequence)
            
            # 5. Extract "Instruments" token (Index 0)
            # This token has attended to all other context
            cls_token = transformed[:, 0, :]
            
            out = self.ln_final(cls_token)
        return out.float()


class TransformerVisualExtractor(BaseFeaturesExtractor):
    """
    Transformer features for instruments/contacts/RWR/mission + a small CNN for ARB visual.

    The visual stream is embedded as an extra token so the 'instruments' token can attend to it.
    """

    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 256,
        n_heads: int = 4,
        n_layers: int = 2,
        visual_cnn_channels: int = 64,
        use_amp: bool = False,
        use_checkpointing: bool = True,
    ):
        super().__init__(observation_space, features_dim)

        self.d_model = int(features_dim)
        self.use_amp = bool(use_amp)
        self._use_checkpointing = bool(use_checkpointing)

        instruments_dim = observation_space["instruments"].shape[0]
        contacts_shape = observation_space["contacts"].shape
        rwr_shape = observation_space["rwr"].shape
        mission_dim = observation_space["mission"].shape[0]
        self.has_proprio = "proprio" in observation_space.spaces

        self.embed_instruments = nn.Linear(instruments_dim, self.d_model)
        self.embed_contact = nn.Linear(contacts_shape[1], self.d_model)
        self.embed_rwr = nn.Linear(rwr_shape[1], self.d_model)
        self.embed_mission = nn.Linear(mission_dim, self.d_model)
        if self.has_proprio:
            proprio_dim = observation_space["proprio"].shape[0]
            self.embed_proprio = nn.Linear(proprio_dim, self.d_model)
        else:
            self.embed_proprio = None

        if "visual" not in observation_space.spaces:
            raise ValueError(
                "TransformerVisualExtractor requires an observation_space with a 'visual' key. "
                "Run env with include_visual=True."
            )

        visual_shape = observation_space["visual"].shape  # (H, W, C) from env
        if len(visual_shape) != 3:
            raise ValueError(f"Expected visual shape (H,W,C), got {visual_shape}")
        self.visual_h, self.visual_w, self.visual_c = int(visual_shape[0]), int(visual_shape[1]), int(visual_shape[2])

        c1 = int(visual_cnn_channels)
        c2 = max(32, c1)
        c3 = max(32, c1)
        if (self.visual_h, self.visual_w) == (48, 96):
            # Preserve the original native-resolution architecture so existing checkpoints remain loadable.
            self.visual_cnn = nn.Sequential(
                nn.Conv2d(self.visual_c, c1, kernel_size=8, stride=4),
                nn.ReLU(),
                nn.Conv2d(c1, c2, kernel_size=4, stride=2),
                nn.ReLU(),
                nn.Conv2d(c2, c3, kernel_size=3, stride=1),
                nn.ReLU(),
                nn.Flatten(),
            )
        else:
            layers: list[nn.Module] = []
            in_ch = self.visual_c
            cur_h = self.visual_h
            cur_w = self.visual_w
            conv_specs = ((c1, 5, 2), (c2, 3, 2), (c3, 3, 1))

            applied = 0
            for out_ch, kernel, stride in conv_specs:
                if cur_h < kernel or cur_w < kernel:
                    continue
                layers.append(nn.Conv2d(in_ch, out_ch, kernel_size=kernel, stride=stride))
                layers.append(nn.ReLU())
                cur_h = (cur_h - kernel) // stride + 1
                cur_w = (cur_w - kernel) // stride + 1
                in_ch = out_ch
                applied += 1

            if applied == 0:
                kernel = 3 if min(cur_h, cur_w) >= 3 else 1
                layers.append(nn.Conv2d(in_ch, c1, kernel_size=kernel, stride=1))
                layers.append(nn.ReLU())
                cur_h = max(1, cur_h - kernel + 1)
                cur_w = max(1, cur_w - kernel + 1)

            layers.append(nn.AdaptiveAvgPool2d((max(1, min(2, cur_h)), max(1, min(4, cur_w)))))
            layers.append(nn.Flatten())
            self.visual_cnn = nn.Sequential(*layers)

        with torch.no_grad():
            sample = torch.zeros((1, self.visual_c, self.visual_h, self.visual_w), dtype=torch.float32)
            n_flatten = int(self.visual_cnn(sample).shape[1])

        self.embed_visual = nn.Linear(n_flatten, self.d_model)

        # Type embeddings: 0=Instruments, 1=Contact, 2=RWR, 3=Mission, 4=Visual, 5=Proprio(optional)
        self.type_embed = nn.Embedding(6 if self.has_proprio else 5, self.d_model)
        self.register_buffer("idx_inst", torch.tensor(0))
        self.register_buffer("idx_contact", torch.tensor(1))
        self.register_buffer("idx_rwr", torch.tensor(2))
        self.register_buffer("idx_mission", torch.tensor(3))
        self.register_buffer("idx_visual", torch.tensor(4))
        if self.has_proprio:
            self.register_buffer("idx_proprio", torch.tensor(5))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(n_heads),
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=int(n_layers), enable_nested_tensor=False)
        self.ln_final = nn.LayerNorm(self.d_model)

    def forward(self, observations: dict) -> torch.Tensor:
        with torch.autocast("cuda", enabled=(torch.cuda.is_available() and self.use_amp)):
            s_inst = observations["instruments"]
            s_contacts = observations["contacts"]
            s_rwr = observations["rwr"]
            s_mission = observations["mission"]

            visual = observations["visual"]
            # Env provides (H,W,C); PyTorch conv expects (C,H,W).
            if visual.ndim != 4:
                raise ValueError(f"Expected visual tensor with 4 dims, got shape={tuple(visual.shape)}")
            if visual.shape[1:] == (self.visual_h, self.visual_w, self.visual_c):
                visual = visual.permute(0, 3, 1, 2)
            elif visual.shape[1:] == (self.visual_c, self.visual_h, self.visual_w):
                pass  # already channel-first
            else:
                raise ValueError(
                    f"Unexpected visual tensor shape={tuple(visual.shape)}; expected "
                    f"(B,{self.visual_h},{self.visual_w},{self.visual_c}) or (B,{self.visual_c},{self.visual_h},{self.visual_w})."
                )
            visual = torch.clamp(visual, -10.0, 10.0)

            emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(self.idx_inst)
            emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(self.idx_mission)

            visual_feat = self.visual_cnn(visual)
            emb_visual = self.embed_visual(visual_feat).unsqueeze(1) + self.type_embed(self.idx_visual)

            emb_contacts = self.embed_contact(s_contacts) + self.type_embed(self.idx_contact)
            emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(self.idx_rwr)
            emb_parts = [emb_inst, emb_mission]
            if self.has_proprio:
                s_proprio = observations["proprio"]
                emb_proprio = self.embed_proprio(s_proprio).unsqueeze(1) + self.type_embed(self.idx_proprio)
                emb_parts.append(emb_proprio)
            sequence = torch.cat([*emb_parts, emb_visual, emb_contacts, emb_rwr], dim=1)

            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint

                x = sequence
                for layer in self.transformer.layers:
                    x = checkpoint(layer, x, use_reentrant=False)
                transformed = x
            else:
                transformed = self.transformer(sequence)

            cls_token = transformed[:, 0, :]
            out = self.ln_final(cls_token)
        return out.float()
