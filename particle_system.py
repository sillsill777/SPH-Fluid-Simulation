import taichi as ti
import numpy as np
import trimesh as tm


@ti.data_oriented
class ParticleSystem:
    def __init__(self, simulation_config):
        self.simulation_config = simulation_config
        self.config = self.simulation_config['Configuration']
        self.rigidBodiesConfig = self.simulation_config['RigidBodies']  # list
        self.fluidBlocksConfig = self.simulation_config['FluidBlocks']  # list

        self.domain_start = np.array(self.config['domainStart'])
        self.domain_end = np.array(self.config['domainEnd'])
        self.particle_radius = self.config['particleRadius']
        self.density0 = self.config['density0']

        self.dim = len(self.domain_start)
        self.domain_size = self.domain_end - self.domain_start
        self.particle_diameter = 2 * self.particle_radius
        self.particle_volume = (4 / 3) * np.pi * (
                self.particle_radius ** self.dim)  # 0.8 * self.particle_diameter ** self.dim
        self.support_length = 4 * self.particle_radius
        self.grid_size = self.support_length
        self.grid_num = np.ceil(self.domain_size / self.grid_size).astype(np.int32)
        self.material_rigid = 0
        self.material_fluid = 1
        self.object_collection = dict()
        self.rigid_object_id = set()

        # ========== Compute number of particles ==========#
        #### Process Fluid Blocks ####
        print("\n=================================================================")
        print("=                        Fluid Blocks                           =")
        print("=================================================================")
        self.total_fluid_particle_num = 0
        for fluid in self.fluidBlocksConfig:
            fluid_particle_num = self.compute_fluid_particle_num(fluid['start'], fluid['end'])
            fluid['particleNum'] = fluid_particle_num
            self.object_collection[fluid['objectId']] = fluid
            self.total_fluid_particle_num += fluid_particle_num
            print("* Object ID: {}         Fluid particle number: {}".format(fluid['objectId'], fluid_particle_num))
            print("-----------------------------------------------------------------")
        print("Total fluid particle number: {}".format(self.total_fluid_particle_num))
        print("-----------------------------------------------------------------")

        print("\n=================================================================")
        print("=                        Rigid Bodies                           =")
        print("=================================================================")
        self.total_rigid_particle_num = 0
        for rigid_body in self.rigidBodiesConfig:
            voxelized_points = self.load_rigid_body(rigid_body)
            rigid_particle_num = voxelized_points.shape[0]
            rigid_body['particleNum'] = rigid_particle_num
            rigid_body['voxelizedPoints']=voxelized_points
            self.object_collection[rigid_body['objectId']]=rigid_body
            self.rigid_object_id.add(rigid_body['objectId'])
            self.total_rigid_particle_num += rigid_particle_num
            print("* Object ID: {}         Rigid Body particle number: {}".format(rigid_body['objectId'],
                                                                                  rigid_particle_num))
            print("-----------------------------------------------------------------")
        print("Total rigid particle number: {}".format(self.total_rigid_particle_num))
        print("-----------------------------------------------------------------")

        self.total_particle_num=self.total_rigid_particle_num+self.total_fluid_particle_num


    def compute_fluid_particle_num(self, start, end):
        particle_num = 1
        for i in range(self.dim):
            particle_num *= len(np.arange(start[i], end[i], self.particle_diameter))
        return particle_num

    def load_rigid_body(self, rigid_body):
        mesh=tm.load(rigid_body['geometryFile'])
        mesh.apply_scale(rigid_body['scale'])
        offset=np.array(rigid_body['translation'])
        rotation_angle=rigid_body['rotationAngle']*np.pi/180
        rotation_axis=rigid_body['rotationAngle']
        rot_matrix=tm.transformations.rotation_matrix(rotation_angle,rotation_axis,mesh.vertices.mean(axis=0))
        mesh.apply_transform(rot_matrix)
        mesh.vertices+=offset
        rigid_body['mesh']=mesh.copy()
        voxelized_mesh=mesh.voxelized(pitch=self.particle_diameter).fill()
        return voxelized_mesh.points
