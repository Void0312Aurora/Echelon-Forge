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
    
    def __init__(self, observation_space: gym.spaces.Dict, features_dim: int = 128, 
                 n_heads: int = 4, n_layers: int = 2):
        # We don't know the exact flattened size in advance easily without calc, 
        # but supers constructor needs it.
        super().__init__(observation_space, features_dim)
        
        self.d_model = features_dim
        
        # 1. Input Projections
        # We assume known shapes from UniversalEnv
        # instruments: (24,) [New Digital Pilot Standard]
        # contacts: (10, 5) -> N=10
        # rwr: (4, 4) -> M=4
        # mission: (4,)
        
        self.embed_instruments = nn.Linear(24, self.d_model)
        self.embed_contact = nn.Linear(5, self.d_model)
        self.embed_rwr = nn.Linear(4, self.d_model)
        self.embed_mission = nn.Linear(4, self.d_model)
        
        # Learnable "Type Embeddings" to distinguish token sources
        # 0=Instruments, 1=Contact, 2=RWR, 3=Mission
        self.type_embed = nn.Embedding(4, self.d_model)
        
        # 2. Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=n_heads,
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # 3. Output Head
        # We just use the first token (Instruments) as the summary representation
        # So no extra pooling layer needed effectively, just identity or layernorm
        self.ln_final = nn.LayerNorm(self.d_model)
        
        # Verification
        # Total tokens = 1 (Self) + 10 (Contacts) + 4 (RWR) + 1 (Mission) = 16
        
    def forward(self, observations: dict) -> torch.Tensor:
        # PPO passes a dict of tensors
        
        # 1. Get Components
        # shapes: (Batch, 24), (Batch, 10, 5), (Batch, 4, 4), (Batch, 4)
        s_inst = observations["instruments"]
        s_contacts = observations["contacts"]
        s_rwr = observations["rwr"]
        s_mission = observations["mission"]
        
        batch_size = s_inst.shape[0]
        
        # 2. Embed
        # (B, 24) -> (B, 1, d_model)
        emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(torch.tensor(0, device=s_inst.device))
        
        # (B, 10, 5) -> (B, 10, d_model)
        emb_contacts = self.embed_contact(s_contacts) + self.type_embed(torch.tensor(1, device=s_contacts.device))
        
        # (B, 4, 4) -> (B, 4, d_model)
        emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(torch.tensor(2, device=s_rwr.device))
        
        # (B, 4) -> (B, 1, d_model)
        emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(torch.tensor(3, device=s_mission.device))
        
        # 3. Concat Sequence
        # Order: [Instruments, Mission, Contacts..., RWR...]
        sequence = torch.cat([emb_inst, emb_mission, emb_contacts, emb_rwr], dim=1)
        # Shape: (B, 16, d_model)
        
        # 4. Transform
        # Masking: We could mask empty contacts/rwr if we had a valid mask. 
        # UniversalEnv pads with 0. 0-padding is a valid input for NN, though attention might check it.
        # For now, we assume all slots are potentially relevant (even 0s imply "empty/no info").
        transformed = self.transformer(sequence)
        
        # 5. Extract "Instruments" token (Index 0)
        # This token has attended to all other context
        cls_token = transformed[:, 0, :]
        
        out = self.ln_final(cls_token)
        return out
