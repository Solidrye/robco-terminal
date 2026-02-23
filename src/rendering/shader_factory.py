import OpenGL.GL as gl
import OpenGL.GL.shaders as shaders

class ShaderFactory:

    @staticmethod
    def create_curvature_shader():
        vertex_shader = """
        #version 460 core
        in vec2 in_position;
        in vec2 in_texCoord;
        out vec2 fragTexCoord;

        void main() {
            fragTexCoord = in_texCoord;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 460 core
        precision highp float;
        in vec2 fragTexCoord;
        out vec4 fragColor;
        uniform sampler2D textureSampler;
        uniform float Frame;
        uniform float Time;
        uniform float Scale;
        uniform vec2 Resolution;
        uniform vec4 Background;
        uniform vec3 BacklightColor;
        uniform float LuminanceIntensity;
        uniform float BloomThreshold;
        uniform sampler2D BloomTexture;
        uniform float BloomStrength;
        uniform float BloomOffset;
        uniform float BloomDepth;
        uniform float BlurStrength;
        uniform float BlurOffset;
        uniform float BlackLevel;
        uniform float ScanlineFactor;
        uniform float GrainIntensity;
        uniform float CurveIntensity;

        #define ENABLE_CURVE 1
        #define ENABLE_OVERSCAN 0
        #define ENABLE_BLOOM 1
        #define ENABLE_BLUR 1
        #define ENABLE_GRAYSCALE 1
        #define ENABLE_BLACKLEVEL 1
        #define ENABLE_REFRESHLINE 1
        #define ENABLE_SCANLINES 1
        #define ENABLE_TINT 1
        #define ENABLE_GRAIN 1
        #define ENABLE_BACKLIGHT 0

        #define OVERSCAN_PERCENTAGE 0.02
        #define BLUR_MULTIPLIER 1.05
        #define GRAYSCALE_INTENSITY 0
        #define GRAYSCALE_GLEAM 0
        #define GRAYSCALE_LUMINANCE 1
        #define GRAYSCALE_LUMA 0
        #define TINT_AMBER vec3(1.0, 0.7, 0.0)
        #define TINT_GREEN vec3(0.0, 1.0, 0.0)
        #define TINT_COLOR TINT_GREEN
        #define SCALED_SCANLINE_PERIOD Scale

        #define clamp01(value) clamp(value, 0.0, 1.0)

        #if ENABLE_BACKLIGHT
        vec3 backlight(vec3 color, vec2 uv) {
            float backlight = max(0.0, dot(normalize(vec3(uv - 0.5, 0.5)), vec3(0.0, 0.0, 1.0)));
            backlight = pow(backlight, 5.0);
            color.rgb += BacklightColor * backlight;
            return clamp01(color);
        }
        #endif

        #if ENABLE_CURVE
        vec2 transformCurve(vec2 uv) {
            uv -= 0.5;
            float r = (uv.x * uv.x + uv.y * uv.y) * CurveIntensity;
            uv *= 4.2 + r;
            uv *= 0.25;
            uv += 0.5;
            return uv;
        }
        #endif

        #if ENABLE_OVERSCAN
        vec4 overscan(vec4 color, in vec2 screenuv, out vec2 uv) {
            uv = screenuv;
            uv -= 0.5;
            uv *= 1.0 / (1.0 - OVERSCAN_PERCENTAGE);
            uv += 0.5;

            if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
                return vec4(Background.rgb * 0.1, 0.0);
            }
            return color;
        }
        #endif

        // Single-pass bloom: sample same texture (textureSampler) so glow is perfectly aligned, no ghosting
        #define BLOOM_KERNEL_SCALE 0.0015
        #if ENABLE_BLOOM
        vec3 bloom(vec3 color, vec2 uv) {
            vec3 bloom = vec3(0.0);
            vec2 texelSize = 1.0 / vec2(textureSize(textureSampler, 0));
            for (int i = -4; i <= 4; i++) {
                for (int j = -4; j <= 4; j++) {
                    vec2 offset = vec2(float(i), float(j)) * texelSize * BLOOM_KERNEL_SCALE;
                    bloom += texture(textureSampler, uv + offset).rgb;
                }
            }
            bloom /= 81.0;
            bloom *= BloomStrength * BloomDepth;
            return clamp01(color + bloom);
        }
        #endif

        #if ENABLE_BLUR
        float blurWeights[9] = float[](0.0, 0.092, 0.081, 0.071, 0.061, 0.051, 0.041, 0.031, 0.021);

        vec3 blurH(vec3 c, vec2 uv) {
            vec3 screen = texture(textureSampler, uv).rgb * 0.102;
            for (int i = 1; i < 9; i++) screen += texture(textureSampler, uv + vec2(float(i) * BlurOffset, 0.0)).rgb * blurWeights[i];
            for (int i = 1; i < 9; i++) screen += texture(textureSampler, uv + vec2(float(-i) * BlurOffset, 0.0)).rgb * blurWeights[i];
            return screen * BLUR_MULTIPLIER;
        }

        vec3 blurV(vec3 c, vec2 uv) {
            vec3 screen = texture(textureSampler, uv).rgb * 0.102;
            for (int i = 1; i < 9; i++) screen += texture(textureSampler, uv + vec2(0.0, float(i) * BlurOffset)).rgb * blurWeights[i];
            for (int i = 1; i < 9; i++) screen += texture(textureSampler, uv + vec2(0.0, float(-i) * BlurOffset)).rgb * blurWeights[i];
            return screen * BLUR_MULTIPLIER;
        }

        vec3 blur(vec3 color, vec2 uv) {
            vec3 blur = (blurH(color, uv) + blurV(color, uv)) / 2.0 - color;
            vec3 blur_mask = blur * BlurStrength;
            return clamp01(color + blur_mask);
        }
        #endif

        #if ENABLE_GRAYSCALE
        vec3 rgb2intensity(vec3 c) {
            return vec3((c.r + c.g + c.b) / 3.0);
        }

        #define GAMMA 2.2
        vec3 gamma(vec3 c) {
            return pow(c, vec3(GAMMA));
        }

        vec3 invGamma(vec3 c) {
            return pow(c, vec3(1.0 / GAMMA));
        }

        vec3 rgb2gleam(vec3 c) {
            c = invGamma(c);
            c = rgb2intensity(c);
            return gamma(c);
        }

        vec3 rgb2luminance(vec3 c) {
            float luminance = dot(c, vec3(0.2126, 0.7152, 0.0722));
            luminance *= LuminanceIntensity;
            return vec3(luminance);
        }

        vec3 rgb2luma(vec3 c) {
            c = invGamma(c);
            c = vec3(0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b);
            return gamma(c);
        }

        vec3 grayscale(vec3 color) {
            #if GRAYSCALE_INTENSITY
            color.rgb = clamp01(rgb2intensity(color.rgb));
            #elif GRAYSCALE_GLEAM
            color.rgb = clamp01(rgb2gleam(color.rgb));
            #elif GRAYSCALE_LUMINANCE
            color.rgb = clamp01(rgb2luminance(color.rgb));
            #elif GRAYSCALE_LUMA
            color.rgb = clamp01(rgb2luma(color.rgb));
            #else
            color.rgb = vec3(1.0, 0.0, 1.0) - color.rgb;
            #endif
            return color;
        }
        #endif

        #if ENABLE_BLACKLEVEL
        vec3 blacklevel(vec3 color) {
            vec3 floor_val = vec3(BlackLevel, BlackLevel, BlackLevel);
            color.rgb -= floor_val;
            color.rgb = clamp01(color.rgb);
            color.rgb += floor_val;
            return clamp01(color);
        }
        #endif

        #if ENABLE_REFRESHLINE
        vec3 refreshLines(vec3 color, vec2 uv) {
            float timeOver = fract(Time / 5.0) * 1.5 - 0.5;
            float refreshLineColorTint = timeOver - uv.y;
            float scanLineWidth = 0.2; // Adjust the width of the scan line
            float gradientFactor = -0.05; // Adjust the gradient intensity
            
            if (uv.y > timeOver && uv.y - scanLineWidth < timeOver) {
                float gradientIntensity = (timeOver - uv.y) / scanLineWidth;
                color.rgb += refreshLineColorTint * gradientIntensity * gradientFactor;
            }
            return clamp01(color);
        }
        #endif

        #if ENABLE_SCANLINES
        float squareWave(float y) {
            return 1.0 - mod(floor(y / SCALED_SCANLINE_PERIOD), 2.0) * ScanlineFactor;
        }

        vec3 scanlines(vec3 color, vec2 pos) {
            float wave = squareWave(pos.y);
            if (length(color.rgb) < 0.2 && false) {
                return clamp01(color + wave * 0.1);
            } else {
                return clamp01(color * wave);
            }
        }
        #endif

        #if ENABLE_TINT
        vec3 tint(vec3 color) {
            color.rgb *= TINT_COLOR;
            return clamp01(color);
        }
        #endif

        #if ENABLE_GRAIN
        float permute(float x) {
            x *= (34.0 * x + 1.0);
            return 289.0 * fract(x * (1.0 / 289.0));
        }

        float rand(inout float state) {
            state = permute(state);
            return fract(state / 41.0);
        }

        #define a0 0.151015505647689
        #define a1 -0.5303572634357367
        #define a2 1.365020122861334
        #define b0 0.132089632343748
        #define b1 -0.7607324991323768

        vec3 grain(vec3 color, vec2 uv) {
            vec3 m = vec3(uv, fract((Time + Frame) / 5.0)) + 1.0; // Updated line
            float state = permute(permute(m.x) + m.y) + m.z;
            float p = 0.95 * rand(state) + 0.025;
            float q = p - 0.5;
            float r2 = q * q;
            float grain = q * (a2 + (a1 * r2 + a0) / (r2 * r2 + b1 * r2 + b0));
            color.rgb += GrainIntensity * grain;
            return clamp01(color);
        }
        #endif

        void main() {
            vec2 uv = fragTexCoord;
            vec4 pos = gl_FragCoord;
            vec2 uv_sample = uv;

            #if ENABLE_CURVE
            vec2 uv_curved = transformCurve(uv);
            uv_sample = uv_curved;

            if (uv_curved.x < -0.025 || uv_curved.y < -0.025) {
                fragColor = vec4(0.0, 0.0, 0.0, 1.0);
                return;
            }
            if (uv_curved.x > 1.025 || uv_curved.y > 1.025) {
                fragColor = vec4(0.0, 0.0, 0.0, 1.0);
                return;
            }
            if (uv_curved.x < -0.015 || uv_curved.y < -0.015) {
                fragColor = vec4(0.03, 0.03, 0.03, 1.0);
                return;
            }
            if (uv_curved.x > 1.015 || uv_curved.y > 1.015) {
                fragColor = vec4(0.03, 0.03, 0.03, 1.0);
                return;
            }
            if (uv_curved.x < -0.001 || uv_curved.y < -0.001) {
                fragColor = vec4(0.0, 0.0, 0.0, 1.0);
                return;
            }
            if (uv_curved.x > 1.001 || uv_curved.y > 1.001) {
                fragColor = vec4(0.0, 0.0, 0.0, 1.0);
                return;
            }
            #endif

            vec4 color = texture(textureSampler, uv_sample);
            // Transparent overlay pixels -> opaque black so text shows on solid background
            if (color.a < 0.5) {
                color = vec4(0.0, 0.0, 0.0, 1.0);
            }

            // Apply bloom threshold (reference: mix bright pixels with bloom; high threshold in pass 1 disables this)
            float luminance = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
            if (luminance > BloomThreshold) {
                vec3 bloomColor = bloom(color.rgb, uv_sample);
                color.rgb = mix(color.rgb, bloomColor, BloomStrength);
            }

            vec2 screenuv = uv_sample;

            #if ENABLE_OVERSCAN
            vec2 uv_overscan;
            color = overscan(color, screenuv, uv_overscan);
            #endif

            #if ENABLE_BLOOM
            color.rgb = bloom(color.rgb, uv_sample);
            #endif

            #if ENABLE_BLUR
            color.rgb = blur(color.rgb, uv_sample);
            #endif

            #if ENABLE_GRAYSCALE
            color.rgb = grayscale(color.rgb);
            #endif

            #if ENABLE_BLACKLEVEL
            color.rgb = blacklevel(color.rgb);
            #endif

            #if ENABLE_REFRESHLINE
            color.rgb = refreshLines(color.rgb, uv_sample);
            #endif

            #if ENABLE_SCANLINES
            color.rgb = scanlines(color.rgb, pos.xy);
            #endif

            #if ENABLE_TINT
            color.rgb = tint(color.rgb);
            #endif

            #if ENABLE_GRAIN
            color.rgb = grain(color.rgb, uv_sample);
            #endif

            #if ENABLE_BACKLIGHT
            color.rgb = backlight(color.rgb, screenuv);
            #endif

            fragColor = color;
        }
        """

        vertex_shader_compiled = shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER)
        fragment_shader_compiled = shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER)
        shader_program = shaders.compileProgram(vertex_shader_compiled, fragment_shader_compiled)

        gl.glUseProgram(shader_program)
        # Set initial uniform values
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "Frame"), 0.0)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "Time"), 0.0)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "Scale"), 1.0)
        gl.glUniform2f(gl.glGetUniformLocation(shader_program, "Resolution"), 800.0, 600.0)
        gl.glUniform4f(gl.glGetUniformLocation(shader_program, "Background"), 0.0, 0.0, 0.0, 1.0)
        gl.glUniform3f(gl.glGetUniformLocation(shader_program, "BacklightColor"), 0.2, 0.2, 0.2)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "LuminanceIntensity"), 2.6)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BloomThreshold"), 0.1)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BloomStrength"), 0.8)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BloomOffset"), 0.0015)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BloomDepth"), 1.0)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BlurStrength"), 0.2)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BlurOffset"), 0.003)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "BlackLevel"), 0.05)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "ScanlineFactor"), 0.3)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "GrainIntensity"), 0.02)
        gl.glUniform1f(gl.glGetUniformLocation(shader_program, "CurveIntensity"), 0.3)

        return shader_program

