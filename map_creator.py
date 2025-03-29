import matplotlib.pyplot as plt

class MapCreator:
    def __init__(self, track_data, checkpoints=None):
        self.track_data = track_data
        self.checkpoints = checkpoints

    def create_map(self, width=5544, height=8192, x_offset=11119.814453125, z_offset=10454.576171875, margin=0, scale_factor=3.30555129051209, drawing_size=10):
        x_coords = [point[1] for point in self.track_data]
        y_coords = [point[2] for point in self.track_data]

        plt.figure(figsize=(10, 6))
        plt.plot(x_coords, y_coords, 'b-')
        plt.title('Shutoku Pist Haritası')
        plt.xlabel('X Koordinatı')
        plt.ylabel('Y Koordinatı')
        plt.grid(True)

        if self.checkpoints:
            for i, checkpoint in enumerate(self.checkpoints):
                world_pos = list(map(float, checkpoint['WORLD_POSITION'].split(',')))
                offset = list(map(float, checkpoint['OFFSET'].split(',')))
                orientation = list(map(float, checkpoint['ORIENTATION'].split(',')))
                plt.text(world_pos[0] + offset[0], world_pos[2] + offset[2], f'Checkpoint {i}',
                         rotation=45, color='red', fontsize=10,
                         bbox=dict(facecolor='white', alpha=0.5))

        plt.show()

# Örnek kullanım:
# track_data = [...]  # Pist verileri
# map_creator = MapCreator(track_data)
# map_creator.create_map()