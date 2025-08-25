# target_project="D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/"
target_project="D:\code\AndroidSourceCodeAnalyzer/app_project/Simple-Notes/app/src/main/"
target_project_source_code=target_project + "kotlin/"
target_project_AndroidManifest =target_project + 'AndroidManifest.xml'
# target_package = 'it.feio.android.omninotes'
target_package = 'com.simplemobiletools.notes.pro'
save_path="./program_analysis_results/" + target_package.replace('.','_') + '/'


# model config
model='deep_seek' 
deep_seek_key="sk-"

filter_mode=True # 是否开启过滤模式

wtg=False

app_name=""

manifest=True

analysis_packages = []

EXCLUSION_PACKAGES = [
    "android.",                      # Android SDK
    "androidx.",                     # AndroidX Support Libraries
    "com.google.android.gms.",       # Google Play Services
    "com.google.firebase.",          # Firebase Libraries
    "com.google.common.",            # Google Guava/Common Libraries
    "com.google.protobuf.",          # Protobuf (often generated)
    "com.google.gson.",              # Gson (JSON library)
    "com.fasterxml.",                # Jackson (JSON library)
    "org.chromium.net.",             # Chromium Network (common in Google apps)
    "org.webrtc.",                   # WebRTC (if not core to your analysis)
    "j$.",                           # Desugared Java features
    "defpackage.",                   # Often obfuscated/generated code markers
    "internal.",                     # Often internal/generated code markers
    "dalvik.",                       # Dalvik/ART internal classes
    "java.",                         # Standard Java Library (excluding specific areas if needed)
    "javax.",                        # Standard Java Extension Library
    "kotlin.",                       # Kotlin standard library
    "kotlinx.",                      # KotlinX libraries
    "scala.",                        # Scala libraries (if applicable)
    "com.squareup.",               # Square libraries (OkHttp, Retrofit, etc.)
    "com.bumptech.glide.",           # Glide image loading
    "com.facebook.yoga.",            # Yoga layout engine
    "io.envoyproxy.",                # Envoy (networking)
    "io.grpc.",                      # gRPC
    "pl.droidsonroids.gif.",         # GIF library
    "com.airbnb.lottie.",            # Lottie animations
    "com.google.code.findbugs.",   # Annotation libraries, etc.
    "org.checkerframework.",         # Annotation libraries
    "org.json.",                     # JSON library
    "org.xmlpull.v1.",               # XML library
    "org.sqlite.",                   # SQLite related
    "org.junit.",                    # Testing framework
    "org.mockito.",                  # Mocking framework
    "junit.",                        # Testing framework
    "android.support.",              # Older Support Libraries
    "com.google.vr.",                # VR libraries
    "com.google.cardboard.",         # Cardboard VR
]