Includes = {
	"buttonstate.fxh"
}

PixelShader =
{
	Samplers =
	{
		MapTexture =
		{
			Index = 0
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}

VertexStruct VS_OUTPUT
{
	float4 vPosition : PDX_POSITION;
	float2 vTexCoord : TEXCOORD0;
};

VertexShader =
{
	MainCode VertexShaderMain
	[[
		VS_OUTPUT main(const VS_INPUT v)
		{
			VS_OUTPUT Out;
			Out.vPosition = mul(WorldViewProjectionMatrix, float4(v.vPosition.xyz, 1));
			Out.vTexCoord = v.vTexCoord;
			return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelShaderMain
	[[
		float4 main(VS_OUTPUT v) : PDX_COLOR
		{
			const float framesPerSecond = 25.0f;
			const float framesPerAtlas = 32.0f;
			const float atlasSlots = 33.0f;
			const float totalFrames = 1075.0f;
			const float durationSeconds = 43.0f;
			float nativeFrame = floor(Offset.x * atlasSlots + 0.5f);
			float overallProgress = (nativeFrame + saturate(AnimationTime)) / atlasSlots;
			float elapsed = overallProgress * durationSeconds;
			float globalFrame = floor(elapsed * framesPerSecond);

			if (globalFrame >= totalFrames)
			{
				return float4(0.0f, 0.0f, 0.0f, 0.0f);
			}

			float activeAtlas = floor(globalFrame / framesPerAtlas);
			float4 atlasMarker = tex2D(MapTexture, float2(0.5f / atlasSlots, 0.5f));
			float thisAtlas = floor(atlasMarker.r * 31.0f + 0.5f)
				+ floor(atlasMarker.g + 0.5f) * 32.0f;
			if (abs(activeAtlas - thisAtlas) > 0.25f)
			{
				return float4(0.0f, 0.0f, 0.0f, 0.0f);
			}

			float localFrame = globalFrame - activeAtlas * framesPerAtlas;
			float localX = clamp(v.vTexCoord.x * atlasSlots, 0.001f, 0.999f);
			float2 atlasUV = float2((1.0f + localFrame + localX) / atlasSlots, v.vTexCoord.y);
			return tex2D(MapTexture, atlasUV);
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}

Effect Up
{
	VertexShader = "VertexShaderMain"
	PixelShader = "PixelShaderMain"
}

Effect Down
{
	VertexShader = "VertexShaderMain"
	PixelShader = "PixelShaderMain"
}

Effect Disable
{
	VertexShader = "VertexShaderMain"
	PixelShader = "PixelShaderMain"
}

Effect Over
{
	VertexShader = "VertexShaderMain"
	PixelShader = "PixelShaderMain"
}
