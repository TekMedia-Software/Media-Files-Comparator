import os
from flask import Flask, render_template, request, redirect, send_file
from pymediainfo import MediaInfo
import shutil

def remove_uploads_directory():
    # Path to the uploads directory
    uploads_dir = 'uploads'

    # Check if the directory exists
    if os.path.exists(uploads_dir):
        shutil.rmtree(uploads_dir)

try:
    app = Flask(__name__)

    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/compare', methods=['POST'])
    def compare():
        if 'file1' not in request.files or 'file2' not in request.files:
            return redirect(request.url)

        file1 = request.files['file1']
        file2 = request.files['file2']

        if file1.filename == '' or file2.filename == '':
            return redirect(request.url)

        file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
        file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
        file1.save(file1_path)
        file2.save(file2_path)

        # Get metadata
        media_info1 = MediaInfo.parse(file1_path)
        media_info2 = MediaInfo.parse(file2_path)

        # Extract metadata into dictionaries
        metadata1 = {track.track_type: track.to_data() for track in media_info1.tracks}
        metadata2 = {track.track_type: track.to_data() for track in media_info2.tracks}

        comparison_data = {
            "Track Type": [],
            "File 1 Metadata": [],
            "File 2 Metadata": []
        }

        def format_key(key):
            """Replace underscores with spaces, reorder specific keys, and capitalize the key."""
            formatted_key = key.replace('_', ' ').capitalize()

            # Reorder specific keys for better readability
            reorder_map = {
                "codecs video": "Video Codecs",
                "codecs audio": "Audio Codecs",
                "channel s": "Channels"
                # Add more mappings if needed
            }

            return reorder_map.get(formatted_key.lower(), formatted_key)


        # Fields to remove from metadata
        fields_to_remove = set([
            'track_type', 'count','' 'count_of_stream_of_this_kind', 'kind_of_stream', 'other_kind_of_stream',
            'video_format_list', 'audio_format_list', 'complete_name', 'folder_name', 'other_format',
            'overall_bit_rate_mode', 'other_overall_bit_rate_mode', 'codecid_compatible',
            'proportion_of_this_stream', 'headersize', 'datasize', 'footersize', 'isstreamable',
            'title', 'movie_name', 'genre', 'file_last_modification_date', 'file_last_modification_date__local',
            'writing_application', 'other_writing_application', 'video_format_withhint_list',
            'audio_format_withhint_list', 'file_name_extension', 'file_name', 'format_extensions_usually_used',
            'commercial_name', 'format_profile', 'internet_media_type', 'codec_id', 'other_codec_id',
            'codec_id_url', 'other_file_size', 'other_duration', 'other_overall_bit_rate', 'other_frame_rate',
            'codec_id_info', 'other_bit_rate', 'other_width', 'other_height', 'stored_height', 'sampled_width',
            'sampled_height', 
            'stream_identifier', 'other_track_id', 'format_info', 'format_settings', 'format_url',
            'format_settings__cabac', 'other_format_settings__cabac', 'format_settings__reference_frames', 
            'other_format_settings__reference_frames', 'rotation', 'other_frame_rate_mode', 'other_chroma_subsampling',
            'other_bit_depth', 'other_scan_type', 'bits__pixel_frame', 'other_stream_size', 'writing_library', 'framerate_mode_original',
            'colour_description_present', 'colour_description_present_source', 'color_range', 'colour_range_source',
            'color_primaries', 'colour_primaries_source', 'transfer_characteristics', 'transfer_characteristics_source',
            'matrix_coefficients', 'matrix_coefficients_source', 'codec_configuration_box', 'other_writing_library',
            'encoded_library_name', 'encoded_library_version', 'encoding_settings', 'mode_extension',
            'maximum_bit_rate', 'other_maximum_bit_rate', 'format_settings__sbr', 'other_format_settings__sbr',
            'format_additionalfeatures', 'source_duration', 'other_source_duration', 'source_duration_lastframe',
            'other_source_duration_lastframe', 'other_bit_rate_mode', 'other_channel_s', 'other_sampling_rate',
            'source_frame_count', 'other_compression_mode', 'source_streamsize_proportion', 'other_source_stream_size',
            'default', 'other_default', 'alternate_group', 'other_alternate_group', 'source_delay', 'source_delay_source',
            'other_bit_rate', 'source_stream_size', 'gsst', 'gstd', 'encoded_date', 'tagged_date', 'overallbitrate_precision_min','overallbitrate_precision_max', 
            'other_delay', 'delay__origin', 'other_delay__origin', 'delay_relative_to_video', 'other_delay_relative_to_video','other_language', 'file_creation_date__local', 'samples_per_frame',
            'stream_size', 'frame_count', 'framerate_den', 'framerate_num', 'samples_count'
        ])

        def format_duration(value):
            """Convert duration in milliseconds to a readable format 'X min Y s'."""
            if isinstance(value, int):
                minutes = value // 60000
                seconds = (value % 60000) // 1000
                return f"{minutes} min {seconds} s"
            return value

        def format_bit_rate(value):
            """Convert overall bit rate to a human-readable format in kb/s."""
            if isinstance(value, int) or isinstance(value, float):
                # Convert bit rate from numeric to kb/s and format with thousands separator
                value_in_kbps = value / 1000  # Convert to kb/s
                formatted_value = f"{value_in_kbps:,.0f}"  # Format with commas and no decimals
                return f"{formatted_value} kb/s"
            return value

        def format_size(value):
            """Convert stream size from bytes to MiB."""
            if isinstance(value, int):
                return f"{value / (1024 * 1024):.2f} MiB"
            return value

        def format_sampling_rate(value):
            """Convert sampling rate to kHz."""
            if isinstance(value, (int, float)):
                return f"{value / 1000:.1f} kHz"
            return value

        def filter_metadata(metadata):
                """Filter out unwanted fields and format keys, add units for numerical fields."""
                filtered_metadata = {}
                for key, value in metadata.items():
                    print(f"Key: {key}, Value: {value}")
                    key = key.strip().lower()  # Normalize the key

                    if key not in fields_to_remove:  # Only process if not in the fields_to_remove list
                        formatted_key = format_key(key)  # Replace underscores and capitalize

                        # Skip fields that start with 'other_' (such as 'other_duration', 'other_file_size')
                        if key.startswith("other_"):
                            continue  # Skip these fields

                        # If the value is a list, we take the first valid entry (if applicable)
                        if isinstance(value, list):
                            value = value[0]  # You can modify this if needed to handle other list entries

                        # Apply specific conversion logic for each field
                        if key == "duration":
                            value = format_duration(value)
                        elif key == "bit_rate" or key == "overall_bit_rate":
                            value = format_bit_rate(value)
                        elif key == "frame_rate":
                            value = value + " FPS"
                        elif key == "stream_size" or key == "file_size":
                            value = format_size(value)
                        elif key == "sampling_rate":
                            value = format_sampling_rate(value)   
                        elif key == "width" or key == "height":
                            value = str(value) + " pixels"              

                        # If the value is a string that contains a unit (like "139 MiB" or "24 FPS"), leave it as is
                        if isinstance(value, str) and " " in value:
                            filtered_metadata[formatted_key] = value
                        else:
                            filtered_metadata[formatted_key] = value

                return filtered_metadata



        # Process the metadata
        all_track_types = ['General', 'Video', 'Audio']
        for track_type in all_track_types:
            if track_type in metadata1 or track_type in metadata2:
                comparison_data["Track Type"].append(track_type)

                file1_metadata = filter_metadata(metadata1.get(track_type, {}))
                file2_metadata = filter_metadata(metadata2.get(track_type, {}))

                comparison_data["File 1 Metadata"].append(file1_metadata if file1_metadata else {"No data": "This track has no relevant metadata."})
                comparison_data["File 2 Metadata"].append(file2_metadata if file2_metadata else {"No data": "This track has no relevant metadata."})

        return render_template('compare.html',
                            comparison_data=comparison_data,
                            file1_name=file1.filename,
                            file2_name=file2.filename)


    if __name__ == '__main__':
        app.run(debug=True, port=5000)

finally:
    remove_uploads_directory()
