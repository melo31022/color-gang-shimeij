from pathlib import Path
import tempfile
import unittest

from color_gang_shimeji.core import parse_actions_xml


class AnimationParserTests(unittest.TestCase):
    def test_reads_pose_frames_and_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "stand.png").write_bytes(b"test")
            (folder / "walk1.png").write_bytes(b"test")
            (folder / "walk2.png").write_bytes(b"test")

            xml = """<?xml version="1.0"?>
            <Mascot xmlns="http://www.group-finity.com/Mascot">
              <ActionList>
                <Action Name="Stand" Type="Stay">
                  <Animation>
                    <Pose Image="/stand.png" ImageAnchor="64,128"
                          Velocity="0,0" Duration="250" />
                  </Animation>
                </Action>
                <Action Name="Walk" Type="Move">
                  <Animation>
                    <Pose Image="/walk1.png" ImageAnchor="64,128"
                          Velocity="-4,0" Duration="2" />
                    <Pose Image="/walk2.png" ImageAnchor="64,128"
                          Velocity="-4,0" Duration="3" />
                  </Animation>
                </Action>
                <Action Name="BehaviorOnly" Type="Sequence">
                  <ActionReference Name="Walk" />
                </Action>
              </ActionList>
            </Mascot>
            """

            result = parse_actions_xml(xml, folder, "Blue", "Blue")

            self.assertEqual(set(result.animations), {"Stand", "Walk"})
            self.assertEqual(len(result.animations["Walk"]), 2)
            self.assertEqual(result.animations["Walk"][0].duration_ms, 20)
            self.assertEqual(result.animations["Walk"][1].duration_ms, 30)
            self.assertEqual(result.animations["Walk"][0].velocity_x, -4)
            self.assertEqual(result.animations["Stand"][0].anchor_y, 128)

    def test_rejects_empty_animation_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                parse_actions_xml(
                    "<Mascot><ActionList><Action Name='NoFrames'/></ActionList></Mascot>",
                    Path(directory),
                    "Blue",
                    "Blue",
                )


if __name__ == "__main__":
    unittest.main()
